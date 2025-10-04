from __future__ import annotations

import json

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from main import (
    python_expression_tool,
    run_agent_loop,
    submit_answer_tool,
)

from config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    TOKEN_COST_DENOMINATOR,
    get_model_pricing,
)
from core.json_io import EnvelopeParseError, parse_envelope
from core.tools import SANDBOX_ENV_VAR, TOOL_HANDLERS, TOOL_SPECS, SandboxError
from tasks.registry import TaskSpec, get_task


SUBMIT_ANSWER_SPEC = {
    "name": "submit_answer",
    "description": "Submit the final answer envelope",
    "input_schema": {
        "type": "object",
        "properties": {"answer": {"description": "JSON envelope"}},
        "required": ["answer"],
    },
}

PYTHON_EXPRESSION_SPEC = {
    "name": "python_expression",
    "description": "Evaluates a Python expression using exec()",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Code executed with limited builtins. Use print() to return output.",
            }
        },
        "required": ["expression"],
    },
}


def _compute_cost(model: str, input_tokens: int | None, output_tokens: int | None) -> tuple[float, float, float]:
    pricing = get_model_pricing(model)
    if not pricing:
        return 0.0, 0.0, 0.0
    input_cost = ((input_tokens or 0) / TOKEN_COST_DENOMINATOR) * pricing["input"]
    output_cost = ((output_tokens or 0) / TOKEN_COST_DENOMINATOR) * pricing["output"]
    total = input_cost + output_cost
    return input_cost, output_cost, total


def _load_auto_answer(metadata: Dict[str, Any]) -> Dict[str, Any] | None:
    path = metadata.get("auto_answer_path")
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None



@dataclass
class RunResult:
    task: str
    run_id: str
    passed: bool
    reward: float
    envelope: Dict[str, Any] | None
    error: str | None
    signals: Dict[str, Any]
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_input: float = 0.0
    cost_output: float = 0.0
    cost_total: float = 0.0


def _build_tools(task: TaskSpec) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = [SUBMIT_ANSWER_SPEC]
    handlers: Dict[str, Any] = {"submit_answer": submit_answer_tool}

    for name in task.tools:
        if name == "python_expression":
            specs.append(PYTHON_EXPRESSION_SPEC)
            handlers["python_expression"] = python_expression_tool
        else:
            tool_spec = TOOL_SPECS.get(name)
            tool_handler = TOOL_HANDLERS.get(name)
            if not tool_spec or not tool_handler:
                raise KeyError(f"Unknown tool configured for task {task.name}: {name}")
            specs.append(tool_spec)
            handlers[name] = tool_handler

    return specs, handlers


def run_task(
    task_name: str,
    run_index: int,
    *,
    verbose: bool = False,
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> RunResult:
    task = get_task(task_name)
    run_id = f"{int(time.time())}_{run_index}"

    sandbox_base = Path(".tmp_sandbox")
    instance = task.build_instance(run_id, base_tmp=sandbox_base)
    sandbox_path = Path(instance["sandbox_path"])
    prompt_vars = instance.get("prompt_vars", {})
    metadata = instance.get("metadata", {})
    prompt = task.load_prompt(prompt_vars)
    skip_agent = bool(metadata.get("skip_agent"))

    tool_specs, tool_handlers = _build_tools(task)

    model_name = model or task.model or DEFAULT_MODEL
    usage_info: Dict[str, int | None] | None = None
    fallback_used = False

    answer_payload = None
    prev_env = None

    if not skip_agent:
        prev_env = os.environ.get(SANDBOX_ENV_VAR)
        os.environ[SANDBOX_ENV_VAR] = str(sandbox_path)

        try:
            answer_payload, usage_info = run_agent_loop(
                prompt=prompt,
                tools=tool_specs,
                tool_handlers=tool_handlers,
                max_steps=task.max_steps,
                model=model_name,
                verbose=verbose,
                temperature=temperature if temperature is not None else task.temperature,
                top_p=top_p if top_p is not None else task.top_p,
                max_tokens=max_tokens if max_tokens is not None else task.max_tokens or DEFAULT_MAX_TOKENS,
                capture_usage=True,
            )
        except SandboxError as exc:
            return RunResult(
                task=task.name,
                run_id=run_id,
                passed=False,
                reward=0.0,
                envelope=None,
                error=str(exc),
                signals={"exception": "sandbox"},
            )
        finally:
            if prev_env is None:
                os.environ.pop(SANDBOX_ENV_VAR, None)
            else:
                os.environ[SANDBOX_ENV_VAR] = prev_env

    input_tokens = usage_info.get("input_tokens") if usage_info else None
    output_tokens = usage_info.get("output_tokens") if usage_info else None
    cost_input, cost_output, cost_total = _compute_cost(model_name, input_tokens, output_tokens)

    if answer_payload is None:
        fallback = _load_auto_answer(metadata)
        if fallback is not None:
            answer_payload = fallback
            fallback_used = True

    if answer_payload is None:
        return RunResult(
            task=task.name,
            run_id=run_id,
            passed=False,
            reward=0.0,
            envelope=None,
            error="Agent did not submit an answer",
            signals={},
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_input=cost_input,
            cost_output=cost_output,
            cost_total=cost_total,
        )

    try:
        parsed_envelope = parse_envelope(answer_payload)
    except EnvelopeParseError as exc:
        if not fallback_used:
            fallback = _load_auto_answer(metadata)
            if fallback is not None:
                answer_payload = fallback
                fallback_used = True
                try:
                    parsed_envelope = parse_envelope(answer_payload)
                except EnvelopeParseError as inner_exc:
                    return RunResult(
                        task=task.name,
                        run_id=run_id,
                        passed=False,
                        reward=0.0,
                        envelope=None,
                        error=str(inner_exc),
                        signals={"invalid_envelope": True},
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_input=cost_input,
                        cost_output=cost_output,
                        cost_total=cost_total,
                    )
            else:
                return RunResult(
                    task=task.name,
                    run_id=run_id,
                    passed=False,
                    reward=0.0,
                    envelope=None,
                    error=str(exc),
                    signals={"invalid_envelope": True},
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_input=cost_input,
                    cost_output=cost_output,
                    cost_total=cost_total,
                )
        else:
            return RunResult(
                task=task.name,
                run_id=run_id,
                passed=False,
                reward=0.0,
                envelope=None,
                error=str(exc),
                signals={"invalid_envelope": True},
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_input=cost_input,
                cost_output=cost_output,
                cost_total=cost_total,
            )

    grade_result = task.grade(parsed_envelope, sandbox_path, metadata)

    return RunResult(
        task=task.name,
        run_id=run_id,
        passed=grade_result.passed,
        reward=grade_result.reward,
        envelope=parsed_envelope,
        error=None,
        signals=grade_result.signals | ({"auto_answer": True} if fallback_used else {}),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_input=cost_input,
        cost_output=cost_output,
        cost_total=cost_total,
    )


def aggregate_results(results: Sequence[RunResult]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    avg_reward = sum(r.reward for r in results) / total if results else 0.0
    input_tokens = sum((r.input_tokens or 0) for r in results)
    output_tokens = sum((r.output_tokens or 0) for r in results)
    cost_input = sum(r.cost_input for r in results)
    cost_output = sum(r.cost_output for r in results)
    cost_total = sum(r.cost_total for r in results)
    return {
        "runs": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total * 100.0) if total else 0.0,
        "avg_reward": avg_reward,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_input": cost_input,
        "cost_output": cost_output,
        "cost_total": cost_total,
    }


def group_by_task(results: Sequence[RunResult]) -> Dict[str, List[RunResult]]:
    grouped: Dict[str, List[RunResult]] = {}
    for result in results:
        grouped.setdefault(result.task, []).append(result)
    return grouped


__all__ = [
    "RunResult",
    "aggregate_results",
    "group_by_task",
    "run_task",
]
