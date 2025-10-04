import argparse
import time

from config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)
from core.runner import run_task

parser = argparse.ArgumentParser(description="Debug a single task with pacing")
parser.add_argument("task")
parser.add_argument("--runs", type=int, default=10)
parser.add_argument("--pause", type=float, default=10.0)
args = parser.parse_args()

for idx in range(args.runs):
    result = run_task(
        args.task,
        idx,
        model=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        max_tokens=DEFAULT_MAX_TOKENS,
        verbose=True,
    )
    print(f"run {idx + 1}: passed={result.passed} reward={result.reward:.2f}")
    print(result.signals)
    if idx + 1 < args.runs:
        time.sleep(args.pause)
