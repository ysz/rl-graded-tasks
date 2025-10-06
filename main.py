import json
import math
import time
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Callable, TypedDict

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from anthropic import Anthropic
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam

from core.tools import TOOL_HANDLERS as CORE_TOOL_HANDLERS
from core.tools import TOOL_SPECS as CORE_TOOL_SPECS
from config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)


class PythonExpressionToolResult(TypedDict):
    result: Any
    error: str | None


class SubmitAnswerToolResult(TypedDict):
    answer: Any
    submitted: bool



def python_expression_tool(expression: str) -> PythonExpressionToolResult:
    """
    Tool that evaluates Python expressions using eval.
    """
    try:
        # Make common modules available
        safe_globals = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "range": range,
            "round": round,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "print": print,
            "sorted": sorted,
        }
        stdout = StringIO()
        with redirect_stdout(stdout):
            exec(expression, safe_globals, {})
        return {"result": stdout.getvalue(), "error": None}
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return {"result": None, "error": str(e)}


def submit_answer_tool(answer: Any) -> SubmitAnswerToolResult:
    """
    Tool for submitting the final answer.
    """
    return {"answer": answer, "submitted": True}


TOOL_SPECS: dict[str, dict[str, Any]] = {
    "python_expression": {
        "name": "python_expression",
        "description": "Evaluates a Python expression",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Will be passed to exec(). Use print() to output something. Returns stdout. ",
                }
            },
            "required": ["expression"],
        },
    },
    "submit_answer": {
        "name": "submit_answer",
        "description": "Submit the final answer",
        "input_schema": {
            "type": "object",
            "properties": {"answer": {"description": "The final answer to submit"}},
            "required": ["answer"],
        },
    },
}
TOOL_SPECS.update(CORE_TOOL_SPECS)


TOOL_HANDLERS: dict[str, Callable] = {
    "python_expression": python_expression_tool,
    "submit_answer": submit_answer_tool,
}
TOOL_HANDLERS.update(CORE_TOOL_HANDLERS)


def _usage_to_dict(usage: Any) -> dict[str, int | None] | None:
    if usage is None:
        return None
    if isinstance(usage, dict):
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
    else:
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
    if input_tokens is None and output_tokens is None:
        return None
    return {
        "input_tokens": int(input_tokens) if input_tokens is not None else None,
        "output_tokens": int(output_tokens) if output_tokens is not None else None,
    }


def run_agent_loop(
    prompt: str,
    tools: list[ToolUnionParam],
    tool_handlers: dict[str, Callable],
    max_steps: int = 5,
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
    temperature: float | None = None,
    top_p: float | None = None,
    stop_sequences: list[str] | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    capture_usage: bool = False,
) -> Any:
    """
    Runs an agent loop with the given prompt and tools.

    Args:
        prompt: The initial prompt for the agent.
        tools: List of tool definitions for the Anthropic API.
        tool_handlers: Mapping from tool names to their handler functions.
        max_steps: Maximum number of steps before stopping.
        model: Anthropic model name to invoke.
        verbose: Whether to print detailed output.
        temperature: Optional sampling temperature override.
        top_p: Optional top-p sampling override.
        stop_sequences: Optional list of stop sequences to apply.
        max_tokens: Token limit for the assistant response.
        capture_usage: When True, also return the latest usage metadata.

    Returns:
        The submitted answer if submit_answer was called, otherwise None.
        When capture_usage is True, returns a tuple of (answer, usage_dict).
    """
    client = Anthropic(timeout=30.0, max_retries=2)
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]
    last_usage: dict[str, int | None] | None = None

    for step in range(max_steps):
        if verbose:
            print(f"\n=== Step {step + 1}/{max_steps} ===")

        request_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "tools": tools,
            "messages": messages,
        }
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if stop_sequences is not None:
            request_kwargs["stop_sequences"] = stop_sequences

        response = None
        for attempt in range(3):
            try:
                response = client.messages.create(**request_kwargs)
                break
            except OverloadedError:
                if attempt == 2:
                    raise
                delay = min(5, 2 ** attempt)
                if verbose:
                    print(
                        "Anthropic API overloaded; retrying in "
                        f"{delay} seconds (attempt {attempt + 2}/3)."
                    )
                time.sleep(delay)
            except Exception as e:
                if verbose:
                    print(f"API error on attempt {attempt + 1}: {type(e).__name__}: {str(e)[:100]}")
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        if response is None:
            raise RuntimeError("Anthropic API did not return a response")
        usage_info = _usage_to_dict(getattr(response, "usage", None))
        if usage_info is not None:
            last_usage = usage_info

        # Track if we need to continue
        has_tool_use = False
        tool_results = []
        submitted_answer = None

        # Process the response
        for content in response.content:
            if content.type == "text":
                if verbose:
                    print(f"Assistant: {content.text}")
            elif content.type == "tool_use":
                has_tool_use = True
                tool_name = content.name

                if tool_name in tool_handlers:
                    if verbose:
                        print(f"Using tool: {tool_name}")

                    # Extract arguments based on tool
                    handler = tool_handlers[tool_name]
                    tool_input = content.input

                    # Call the appropriate tool handler
                    try:
                        if tool_name == "python_expression":
                            assert (
                                isinstance(tool_input, dict) and "expression" in tool_input
                            )
                            if verbose:
                                print("\nInput:")
                                print("```")
                                for line in tool_input["expression"].split("\n"):
                                    print(f"{line}")
                                print("```")
                            result = handler(tool_input["expression"])
                            if verbose:
                                print("\nOutput:")
                                print("```")
                                print(result)
                                print("```")
                        elif tool_name == "submit_answer":
                            assert isinstance(tool_input, dict) and "answer" in tool_input
                            result = handler(tool_input["answer"])
                            submitted_answer = result["answer"]
                        else:
                            # Generic handler call
                            result = (
                                handler(**tool_input)
                                if isinstance(tool_input, dict)
                                else handler(tool_input)
                            )
                    except KeyboardInterrupt:
                        raise
                    except Exception as exc:
                        result = {"error": str(exc)}

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": json.dumps(result),
                        }
                    )

        # If we have tool uses, add them to the conversation
        if has_tool_use:
            messages.append({"role": "assistant", "content": response.content})

            messages.append({"role": "user", "content": tool_results})

            # If an answer was submitted, return it
            if submitted_answer is not None:
                if verbose:
                    print(f"\nAgent submitted answer: {submitted_answer}")
                if capture_usage:
                    return submitted_answer, last_usage
                return submitted_answer
        else:
            # No tool use, conversation might be complete
            if verbose:
                print("\nNo tool use in response, ending loop.")
            break

    if verbose:
        print(f"\nReached maximum steps ({max_steps}) without submitting answer.")
    if capture_usage:
        return None, last_usage
    return None


def main():
    tools: list[ToolUnionParam] = [
        TOOL_SPECS["python_expression"],
        TOOL_SPECS["submit_answer"],
    ]

    tool_handlers = {
        "python_expression": TOOL_HANDLERS["python_expression"],
        "submit_answer": TOOL_HANDLERS["submit_answer"],
    }

    # Run the test 10 times and track success rate
    num_runs = 10
    expected_answer = 8769
    successes = 0

    print(f"Running {num_runs} test iterations...")
    print("=" * 60)

    for i in range(num_runs):
        print(f"\n\n{'=' * 20} RUN {i + 1}/{num_runs} {'=' * 20}")

        result = run_agent_loop(
            prompt="Calculate (2^10 + 3^5) * 7 - 100. Use the python_expression tool and then submit the answer.",
            tools=tools,
            tool_handlers=tool_handlers,
            max_steps=5,
            verbose=False,  # Set to False for cleaner output during multiple runs
            max_tokens=1000,
        )

        if result == expected_answer:
            print(f"✓ Run {i + 1}: SUCCESS - Got {result}")
            successes += 1
        else:
            print(f"✗ Run {i + 1}: FAILURE - Got {result}, expected {expected_answer}")

    # Calculate and display pass rate
    pass_rate = (successes / num_runs) * 100
    print(f"\n{'=' * 60}")
    print("Test Results:")
    print(f"  Passed: {successes}/{num_runs}")
    print(f"  Failed: {num_runs - successes}/{num_runs}")
    print(f"  Pass Rate: {pass_rate:.1f}%")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
