from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

_SANDBOX_BASE = Path(".tmp_sandbox")
_FIXTURE_DIR = Path(__file__).parent / "fixture"

CASES = [
    {
        "title": "collapse double hyphen",
        "input": "Config -- Reload",
        "expected": "config-reload",
    },
    {
        "title": "trim border hyphen",
        "input": "--release--",
        "expected": "release",
    },
    {
        "title": "german umlaut",
        "input": "Überraschung",
        "expected": "ueberraschung",
    },
    {
        "title": "mixed special chars",
        "input": "Café---Bar",
        "expected": "cafe-bar",
    },
    {
        "title": "complex trim",
        "input": "---Test---Case---",
        "expected": "test-case",
    },
]


def _render_layout(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        entries.append(f"- {path.relative_to(root).as_posix()}")
    return "\n".join(entries)


def build_instance(run_id: str, base_tmp: Path | None = None) -> dict[str, object]:
    base = base_tmp or _SANDBOX_BASE
    base.mkdir(parents=True, exist_ok=True)
    sandbox = base / f"run_{run_id}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    project_root = sandbox / "project"
    shutil.copytree(_FIXTURE_DIR, project_root)

    cases_path = project_root / "tests" / "data" / "cases.json"
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    cases_path.write_text(json.dumps(CASES, indent=2), encoding="utf-8")

    layout_hint = _render_layout(sandbox)

    return {
        "sandbox_path": sandbox,
        "prompt_vars": {"layout_hint": layout_hint},
        "metadata": {},
    }


__all__ = ["build_instance"]
