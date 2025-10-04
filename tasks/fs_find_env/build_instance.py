from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import Dict, List

_SANDBOX_BASE = Path(".tmp_sandbox")


def _write_file(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _render_layout(root: Path) -> str:
    files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    if not files:
        return "(empty sandbox)"
    return "\n".join(f"- {entry}" for entry in files)


def build_instance(run_id: str, base_tmp: Path | None = None) -> Dict[str, object]:
    base = base_tmp or _SANDBOX_BASE
    base.mkdir(parents=True, exist_ok=True)
    sandbox = base / f"run_{run_id}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    rng = random.Random(run_id)
    variant = rng.randint(1, 3)

    expected: List[str] = []

    # Common noise files
    _write_file(sandbox, "README.txt", "Sample project snapshot")
    _write_file(
        sandbox,
        "tests/.env.fixture",
        "SECRET=should_be_skipped\n",
    )
    _write_file(sandbox, "tests/unit/.env.dev", "SECRET=not_counted\n")
    _write_file(sandbox, "notes/.env.template", "# SECRET=placeholder\n")
    _write_file(sandbox, "notes/.env.backup", "# SECRET=archived\n")

    if variant == 1:
        _write_file(sandbox, ".env", "# baseline env\nSECRET=root_key\n")
        _write_file(sandbox, "config/.env.production", "SECRET=prod_key\n")
        _write_file(sandbox, "config/.env.sample", "# SECRET=placeholder\n")
        expected.extend([
            ".env",
            "config/.env.production",
        ])
    elif variant == 2:
        _write_file(sandbox, "services/payment/.env", "SECRET=pay_key\n")
        _write_file(sandbox, "services/payment/.env.backup", "SECRET=old_key\n")
        _write_file(sandbox, "services/payment/.env.example", "# SECRET=placeholder\n")
        expected.extend([
            "services/payment/.env",
            "services/payment/.env.backup",
        ])
    else:
        _write_file(sandbox, "deploy/.env.staging", "# comment\nSECRET=stage_value\n")
        _write_file(sandbox, "deploy/.env.local", "SECRET=local_value\n")
        _write_file(sandbox, "deploy/.env.sample", "# SECRET=dummy\n")
        _write_file(sandbox, "deploy/readme.txt", "Documenting staging secrets stay commented\n")
        expected.extend([
            "deploy/.env.local",
            "deploy/.env.staging",
        ])

    layout_hint = _render_layout(sandbox)
    return {
        "sandbox_path": sandbox,
        "prompt_vars": {"layout_hint": layout_hint},
        "metadata": {
            "expected_paths": sorted(expected),
            "variant": variant,
        },
    }


__all__ = ["build_instance"]
