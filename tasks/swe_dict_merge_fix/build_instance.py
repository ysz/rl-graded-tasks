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
            "title": "Nested merge with partial override",
            "base": {"config": {"db": {"host": "localhost", "port": 5432}}},
            "patch": {"config": {"db": {"port": 3306}}},
            "expected": {"config": {"db": {"host": "localhost", "port": 3306}}},
        },
        {
            "title": "Multiple branches",
            "base": {
                "services": {
                    "api": {"host": "localhost"},
                    "worker": {"threads": 4},
                }
            },
            "patch": {
                "services": {
                    "api": {"port": 9090},
                }
            },
            "expected": {
                "services": {
                    "api": {"host": "localhost", "port": 9090},
                    "worker": {"threads": 4},
                }
            },
        },
    ],
    2: [
        {
            "title": "Three level nesting",
            "base": {
                "app": {
                    "cache": {"redis": {"host": "localhost"}},
                    "db": {"primary": {"host": "db1"}},
                }
            },
            "patch": {
                "app": {
                    "cache": {"redis": {"port": 6379}},
                }
            },
            "expected": {
                "app": {
                    "cache": {"redis": {"host": "localhost", "port": 6379}},
                    "db": {"primary": {"host": "db1"}},
                }
            },
        },
        {
            "title": "Deep nested with list",
            "base": {"app": {"middleware": {"stack": ["cors", "auth"]}}},
            "patch": {"app": {"middleware": {"stack": ["auth", "cache"]}}},
            "expected": {"app": {"middleware": {"stack": ["auth", "cache"]}}},
        },
    ],
    3: [
        {
            "title": "Preserve unrelated nested keys",
            "base": {
                "env": {
                    "prod": {"region": "eu", "size": "large"},
                    "dev": {"region": "us"},
                }
            },
            "patch": {
                "env": {
                    "prod": {"region": "us"},
                }
            },
            "expected": {
                "env": {
                    "prod": {"region": "us", "size": "large"},
                    "dev": {"region": "us"},
                }
            },
        },
        {
            "title": "Add nested structure",
            "base": {"features": {"logging": {"level": "info"}}},
            "patch": {"features": {"analytics": {"enabled": True}}},
            "expected": {
                "features": {
                    "logging": {"level": "info"},
                    "analytics": {"enabled": True},
                }
            },
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

    # Clean up old sandbox directories if too many exist
    if base.exists():
        existing = sorted(base.glob("run_*"), key=lambda p: p.stat().st_mtime)
        if len(existing) > 50:  # Keep only 50 most recent
            for old_dir in existing[:-50]:
                try:
                    shutil.rmtree(old_dir)
                except Exception:
                    pass

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
