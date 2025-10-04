from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from typing import Dict, List

_SANDBOX_BASE = Path(".tmp_sandbox")
_FIXTURE_DIR = Path(__file__).parent / "fixture"

_VARIANTS: Dict[int, List[Dict[str, object]]] = {
    1: [
        {
            "title": "Deep merge with overrides",
            "base": {"app": {"host": "localhost", "port": 8000}},
            "patch": {"app": {"port": 9000, "debug": True}},
            "expected": {"app": {"host": "localhost", "port": 9000, "debug": True}},
        },
        {
            "title": "List replacement",
            "base": {"plugins": ["auth", "cache"]},
            "patch": {"plugins": ["auth", "metrics"]},
            "expected": {"plugins": ["auth", "metrics"]},
        },
    ],
    2: [
        {
            "title": "Multiple branches",
            "base": {"app": {"cache": {"enabled": False}}, "version": 1},
            "patch": {"app": {"cache": {"enabled": True, "ttl": 30}}, "version": 2},
            "expected": {"app": {"cache": {"enabled": True, "ttl": 30}}, "version": 2},
        },
        {
            "title": "Insert nested dict",
            "base": {"services": {}},
            "patch": {"services": {"payment": {"url": "https://pay"}}},
            "expected": {"services": {"payment": {"url": "https://pay"}}},
        },
    ],
    3: [
        {
            "title": "Preserve unrelated keys",
            "base": {"env": {"prod": {"region": "eu"}, "dev": {"region": "us"}}},
            "patch": {"env": {"prod": {"region": "us", "replicas": 3}}},
            "expected": {
                "env": {
                    "prod": {"region": "us", "replicas": 3},
                    "dev": {"region": "us"},
                }
            },
        },
        {
            "title": "Replace primitive",
            "base": {"feature": {"enabled": False}},
            "patch": {"feature": {"enabled": True}},
            "expected": {"feature": {"enabled": True}},
        },
    ],
}


def _render_layout(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        entries.append(f"- {path.relative_to(root).as_posix()}")
    return "\n".join(entries) if entries else "(empty sandbox)"


def _write_cases(project_root: Path, cases: List[Dict[str, object]]) -> None:
    data_path = project_root / "tests" / "data" / "cases.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8") as fh:
        json.dump(cases, fh, indent=2)


def build_instance(run_id: str, base_tmp: Path | None = None) -> Dict[str, object]:
    base = base_tmp or _SANDBOX_BASE
    base.mkdir(parents=True, exist_ok=True)
    sandbox = base / f"run_{run_id}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    project_root = sandbox / "project"
    shutil.copytree(_FIXTURE_DIR, project_root)

    rng = random.Random(run_id)
    variant = rng.randint(1, len(_VARIANTS))
    cases = _VARIANTS[variant]
    _write_cases(project_root, cases)

    layout_hint = _render_layout(sandbox)

    return {
        "sandbox_path": sandbox,
        "prompt_vars": {"layout_hint": layout_hint, "variant": variant},
        "metadata": {"variant": variant, "cases": cases},
    }


__all__ = ["build_instance"]
