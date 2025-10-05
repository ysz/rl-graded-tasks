from __future__ import annotations

import argparse
import time
from typing import List

from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables from .env file
load_dotenv()

from config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)
from core.runner import aggregate_results, group_by_task, run_task
from tasks.registry import TASK_REGISTRY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run task evaluations")
    parser.add_argument("--task", help="Name of the task to run", choices=sorted(TASK_REGISTRY.keys()))
    parser.add_argument("--runs", type=int, default=10, help="Number of runs per task")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Anthropic model name")
    parser.add_argument("--verbose", action="store_true", help="Print agent loop details")
    parser.add_argument("--pause", type=float, default=0.0, help="Seconds to sleep between runs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task_names: List[str]
    if args.task:
        task_names = [args.task]
    else:
        task_names = list(TASK_REGISTRY.keys())

    print(f"Starting evaluation: {args.runs} runs of tasks: {task_names}", flush=True)
    results = []
    for task_name in task_names:
        for run_index in range(args.runs):
            start_time = time.time()
            print(f"[{run_index + 1}/{args.runs}] Starting {task_name}...", end=" ", flush=True)
            try:
                result = run_task(
                    task_name,
                    run_index,
                    verbose=args.verbose,
                    model=args.model,
                    temperature=DEFAULT_TEMPERATURE,
                    top_p=DEFAULT_TOP_P,
                    max_tokens=DEFAULT_MAX_TOKENS,
                )
                results.append(result)
                elapsed = time.time() - start_time
                status = "✓ PASS" if result.passed else "✗ FAIL"
                print(f"{status} (reward={result.reward:.2f}, {elapsed:.1f}s)", flush=True)
                if args.verbose:
                    print(f"  Tokens: {result.input_tokens or 0} in, {result.output_tokens or 0} out", flush=True)
            except KeyboardInterrupt:
                print("\nInterrupted by user", flush=True)
                raise
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"✗ ERROR ({elapsed:.1f}s): {type(e).__name__}: {str(e)[:80]}", flush=True)
                # Continue with next run instead of failing completely

            if args.pause > 0 and run_index + 1 < args.runs:
                time.sleep(args.pause)
            elif run_index + 1 < args.runs:
                # Always add small delay to avoid rate limits
                time.sleep(0.5)

    grouped = group_by_task(results)
    table_rows = []
    total_tokens_in = 0
    total_tokens_out = 0
    total_cost_in = 0.0
    total_cost_out = 0.0
    total_cost = 0.0
    for task_name in task_names:
        summary = aggregate_results(grouped.get(task_name, []))
        table_rows.append(
            [
                task_name,
                summary.get("passed", 0),
                summary.get("failed", 0),
                f"{summary.get('pass_rate', 0.0):.1f}%",
                f"{summary.get('avg_reward', 0.0):.2f}",
                summary.get("input_tokens", 0),
                summary.get("output_tokens", 0),
                f"{summary.get('cost_input', 0.0):.4f}",
                f"{summary.get('cost_output', 0.0):.4f}",
                f"{summary.get('cost_total', 0.0):.4f}",
            ]
        )
        total_tokens_in += summary.get("input_tokens", 0)
        total_tokens_out += summary.get("output_tokens", 0)
        total_cost_in += summary.get("cost_input", 0.0)
        total_cost_out += summary.get("cost_output", 0.0)
        total_cost += summary.get("cost_total", 0.0)

    if table_rows:
        headers = [
            "Task",
            "Passed",
            "Failed",
            "Pass Rate",
            "Avg Reward",
            "Tokens In",
            "Tokens Out",
            "Cost In ($)",
            "Cost Out ($)",
            "Cost Total ($)",
        ]
        print(tabulate(table_rows, headers=headers, tablefmt="github"))
        print(f"Total tokens: in={total_tokens_in} out={total_tokens_out}")
        print(f"Total cost: input=${total_cost_in:.4f} output=${total_cost_out:.4f} total=${total_cost:.4f}")


if __name__ == "__main__":
    main()
