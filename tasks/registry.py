from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Sequence

from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_TOP_P
from core.grading import GradeResult

TASKS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class TaskSpec:
    name: str
    prompt_path: Path
    build_instance: Callable[[str, Path | None], Dict[str, Any]]
    grade: Callable[[Any, Path, Dict[str, Any]], GradeResult]
    tools: Sequence[str]
    max_steps: int = 6
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_tokens: int = 600

    def load_prompt(self, variables: Mapping[str, Any] | None = None) -> str:
        template = self.prompt_path.read_text()
        return template.format(**(variables or {}))


from tasks.fs_find_env.build_instance import build_instance as fs_build_instance
from tasks.fs_find_env.grade import grade as fs_grade


from tasks.logs_top5xx.build_instance import build_instance as logs_build_instance
from tasks.logs_top5xx.grade import grade as logs_grade
from tasks.sql_q2_revenue.build_instance import build_instance as sql_build_instance
from tasks.sql_q2_revenue.grade import grade as sql_grade
from tasks.swe_dict_merge_fix.build_instance import build_instance as dict_build_instance
from tasks.swe_dict_merge_fix.grade import grade as dict_grade
from tasks.swe_slugify_fix.build_instance import build_instance as slug_build_instance
from tasks.swe_slugify_fix.grade import grade as slug_grade


TASK_REGISTRY: Dict[str, TaskSpec] = {
    "fs_find_env": TaskSpec(
        name="fs_find_env",
        prompt_path=TASKS_DIR / "fs_find_env" / "prompt.md",
        build_instance=fs_build_instance,
        grade=fs_grade,
        tools=("glob_find", "grep_search", "file_read"),
        max_steps=8,
        max_tokens=600,
    ),
    "swe_slugify_fix": TaskSpec(
        name="swe_slugify_fix",
        prompt_path=TASKS_DIR / "swe_slugify_fix" / "prompt.md",
        build_instance=slug_build_instance,
        grade=slug_grade,
        tools=("file_read", "run_pytests"),
        max_steps=4,
        max_tokens=400,
        temperature=0.5,
    ),
    "swe_dict_merge_fix": TaskSpec(
        name="swe_dict_merge_fix",
        prompt_path=TASKS_DIR / "swe_dict_merge_fix" / "prompt.md",
        build_instance=dict_build_instance,
        grade=dict_grade,
        tools=("file_read", "file_write", "run_pytests"),
        max_steps=6,
        max_tokens=600,
    ),
    "logs_top5xx": TaskSpec(
        name="logs_top5xx",
        prompt_path=TASKS_DIR / "logs_top5xx" / "prompt.md",
        build_instance=logs_build_instance,
        grade=logs_grade,
        tools=("file_read", "grep_search", "python_expression"),
        max_steps=5,
        max_tokens=500,
    ),
    "sql_q2_revenue": TaskSpec(
        name="sql_q2_revenue",
        prompt_path=TASKS_DIR / "sql_q2_revenue" / "prompt.md",
        build_instance=sql_build_instance,
        grade=sql_grade,
        tools=("duckdb_sql", "file_read", "python_expression"),
        max_steps=6,
        max_tokens=700,
    ),
}


def get_task(name: str) -> TaskSpec:
    try:
        return TASK_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown task: {name}") from exc


__all__ = ["TaskSpec", "TASK_REGISTRY", "get_task"]
