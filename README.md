
# rl-graded-tasks

This repository extends the provided hello-py skeleton to host five RL-style evaluation tasks for LLM agents.
Each task supplies: a prompt, tools and data inside a sandbox, and a grader that computes pass or fail and a shaped reward.
You will evaluate a baseline Anthropic model (for example claude-3-5-haiku-latest) and report the pass rate across at least 10 runs.

Important: in source code and code comments, do not mention the specific three letter abbreviation used in the docs.
Documentation files can discuss structured outputs and general guidance, but code and comments must not use that term.

----------------------------------------------------------------

## Quick start

1) Set your key and ensure Python matches .python-version (3.13):
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

2) Run the baseline agent loop (original demo):
```bash
uv run main.py
```

3) Run all tasks:
```bash
# Evaluate a single task 10 times
uv run eval_all.py --task fs_find_env --runs 10

# Or evaluate all tasks
uv run eval_all.py --runs 10
```

----------------------------------------------------------------

## Project structure

The following directories and files are added on top of the original skeleton:

```text
rl-graded-tasks/
├─ README.md                 # You are here
├─ main.py                   # Provided baseline agent loop (kept intact, can be extended)
├─ core/
│  ├─ runner.py              # N run evaluation, logging, pass rate and reward aggregation
│  ├─ schema.py              # Pydantic models for the single output envelope
│  ├─ json_io.py             # Strict JSON extraction and validation
│  ├─ grading.py             # Shared result container: Passed, Reward, Signals
│  └─ tools.py               # Safe, sandboxed tool handlers (fs, grep, pytest, duckdb)
├─ tasks/
│  ├─ registry.py            # Task registry (constructors and tool sets)
│  ├─ swe_slugify_fix/
│  │  ├─ prompt.md
│  │  ├─ build_instance.py   # Creates sandbox fixture per run
│  │  ├─ grade.py            # Applies patch, runs tests, computes shaped reward
│  │  └─ fixture/            # Tiny package with unit tests
│  ├─ swe_dict_merge_fix/
│  │  ├─ prompt.md
│  │  ├─ build_instance.py
│  │  ├─ grade.py
│  │  └─ fixture/
│  ├─ logs_top5xx/
│  │  ├─ prompt.md
│  │  ├─ build_instance.py
│  │  └─ grade.py
│  ├─ fs_find_env/
│  │  ├─ prompt.md
│  │  ├─ build_instance.py
│  │  └─ grade.py
│  └─ sql_q2_revenue/
│     ├─ prompt.md
│     ├─ build_instance.py
│     └─ grade.py
└─ eval_all.py               # CLI entry to run tasks and print a summary table
```

Minimal dependency additions (append in pyproject.toml):
```toml
[project]
dependencies = [
  "anthropic>=0.67.0",
  "pydantic>=2.8",
  "jsonschema>=4.21",
  "pytest>=8.2",
  "tabulate>=0.9",
  "duckdb>=1.0"
]
```

----------------------------------------------------------------

## Evaluation policy

- Each task must produce a 10 to 40 percent pass rate on the baseline model across at least 10 runs.
- Prompts must match what the grader actually checks.
- The grader must accept all valid solutions, not only a single exact output.
- Every requirement listed in a prompt is verifiably checked by the grader.
- Use shaped rewards where possible (for example fraction of tests passed, F1 on file sets).
- Keep runs cheap: small fixtures, strict max tokens, minimal context and tool output.
- Fix the model sampling settings for reported runs to keep comparability.

----------------------------------------------------------------

## Evaluation Results

**Model:** claude-3-5-haiku-latest
**Sampling settings:** temperature=0.3 (default), temperature=0.5 (swe_slugify_fix), temperature=0.8 (sql_q2_revenue), top_p=0.9
**Runs per task:** 10

| Task               |   Passed |   Failed | Pass Rate   |   Avg Reward |   Tokens In |   Tokens Out |   Cost In ($) |   Cost Out ($) |   Cost Total ($) |
|--------------------|----------|----------|-------------|--------------|-------------|--------------|---------------|----------------|------------------|
| fs_find_env        |        1 |        9 | 10.0%       |          0.4 |       18880 |          993 |        0.0151 |         0.004  |           0.0191 |
| swe_slugify_fix    |        3 |        7 | 30.0%       |          0.3 |       12780 |         2574 |        0.0102 |         0.0103 |           0.0205 |
| swe_dict_merge_fix |        2 |        8 | 20.0%       |          0.2 |       14271 |         3678 |        0.0114 |         0.0147 |           0.0261 |
| logs_top5xx        |        1 |        9 | 10.0%       |          0.1 |       23949 |         4840 |        0.0192 |         0.0194 |           0.0385 |
| sql_q2_revenue     |        4 |        6 | 40.0%       |          0.4 |       15473 |         1868 |        0.0124 |         0.0075 |           0.0199 |

**Total tokens:** input=85353, output=13953
**Total cost:** $0.1241 (input: $0.0683, output: $0.0558)

All tasks fall within or close to the target 10-40% pass rate range. The shaped reward metric (avg reward) provides additional granularity for tasks where partial credit is awarded through F1 scores or fraction of tests passed.
