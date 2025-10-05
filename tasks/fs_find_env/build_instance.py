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
    variant = rng.randint(1, 6)

    expected: List[str] = []

    # Common noise files
    _write_file(sandbox, "README.txt", "Sample project snapshot")
    _write_file(
        sandbox,
        "tests/.env.fixture",
        "SECRET=should_be_skipped\n",
    )

    # Tricky cases that should NOT match (only most important ones)
    _write_file(sandbox, "lib/.env.test", " SECRET=indented\nVAR=value\n")  # Leading space
    _write_file(sandbox, "docs/.env.sample", "# SECRET=commented\n")  # Only commented

    if variant == 1:
        _write_file(sandbox, ".env", "# baseline env\nSECRET=root_key\n")
        _write_file(sandbox, "config/.env.production", "SECRET=prod_key\n")
        _write_file(sandbox, "config/.env.sample", "# SECRET=placeholder\n")
        _write_file(sandbox, "scripts/.env.build", "BUILD_SECRET=not_matching\n")
        _write_file(sandbox, "temp/.env.backup", "# SECRET=old\n")
        expected.extend([
            ".env",
            "config/.env.production",
        ])
    elif variant == 2:
        _write_file(sandbox, "services/.env", "SECRET=pay_key\n")
        _write_file(sandbox, "services/.env.backup", "SECRET=old_key\n")
        _write_file(sandbox, "services/.env.example", "# SECRET=placeholder\n")
        _write_file(sandbox, "api/.env.dev", "SECRET=api_dev\n")
        _write_file(sandbox, "api/.env.test", "TEST=value\n")  # No SECRET
        _write_file(sandbox, "web/.env.cache", " SECRET=has_space\n")  # Leading space
        expected.extend([
            "api/.env.dev",
            "services/.env",
            "services/.env.backup",
        ])
    elif variant == 3:
        _write_file(sandbox, "deploy/.env.staging", "# comment\nSECRET=stage_value\n")
        _write_file(sandbox, "deploy/.env.local", "SECRET=local_value\n")
        _write_file(sandbox, "deploy/.env.sample", "# SECRET=dummy\n")
        expected.extend([
            "deploy/.env.local",
            "deploy/.env.staging",
        ])
    elif variant == 4:
        _write_file(sandbox, "app/.env", "SECRET=app_secret\n")
        _write_file(sandbox, ".configs/.env.global", "SECRET=global\n")
        _write_file(sandbox, "backend/.env.prod", "# All commented\n# SECRET=commented\n")
        _write_file(sandbox, "worker/.env.queue", "SECRET=worker_secret\n")
        _write_file(sandbox, "worker/.env.old", "# SECRET=archived\n")
        _write_file(sandbox, "data/.env.cache", "export SECRET=value\n")  # Has prefix
        expected.extend([
            ".configs/.env.global",
            "app/.env",
            "worker/.env.queue",
        ])
    elif variant == 5:
        _write_file(sandbox, ".env.development", "SECRET=dev_key\n")
        _write_file(sandbox, "src/.env", "DEBUG=true\nSECRET=src_secret\nLOG_LEVEL=info\n")
        _write_file(sandbox, "cache/.env.temp", "CACHE_SECRET=not_matching\n")
        _write_file(sandbox, "build/.env.ci", "# SECRET=ci_secret\n")
        _write_file(sandbox, "public/.env.static", "STATIC_SECRET=value\n")
        expected.extend([
            ".env.development",
            "src/.env",
        ])
    else:
        # Variant 6: Moderate case
        _write_file(sandbox, ".env.prod", "SECRET=production\n")
        _write_file(sandbox, "app/.env.config", "SECRET=app_config\n")
        _write_file(sandbox, "tools/.env.helper", "HELPER=value\n")  # No SECRET
        expected.extend([
            ".env.prod",
            "app/.env.config",
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
