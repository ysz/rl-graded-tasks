from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from core.grading import GradeResult
from core.json_io import EnvelopeParseError, parse_envelope


def _strip_diff_prefixes(patch_text: str) -> str:
    """Remove leading a/ and b/ prefixes so patch -p0 accepts git-style diffs."""

    lines = []
    def _normalize_header(prefix: str, line: str) -> str:
        body = line[len(prefix) :].strip()
        if body.startswith("a/") or body.startswith("b/"):
            body = body[2:]
        if body == "slugify.py":
            body = "project/slugify/slugify.py"
        return f"{prefix}{body}\n"

    for raw_line in patch_text.splitlines(keepends=True):
        if raw_line.startswith("--- "):
            lines.append(_normalize_header("--- ", raw_line))
        elif raw_line.startswith("+++ "):
            lines.append(_normalize_header("+++ ", raw_line))
        else:
            lines.append(raw_line)
    return "".join(lines)


def _apply_patch(patch_text: str, sandbox: Path) -> tuple[bool, str]:
    sanitized = _strip_diff_prefixes(patch_text)
    proc = subprocess.run(
        ["patch", "-p0"],
        input=sanitized,
        text=True,
        cwd=str(sandbox),
        capture_output=True,
    )
    success = proc.returncode == 0
    message = "\n".join(filter(None, [proc.stdout.strip(), proc.stderr.strip()]))
    return success, message


def _run_pytest(project_root: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["pytest", "-q"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def grade(envelope: Any, sandbox_path: Path, metadata: Dict[str, Any]) -> GradeResult:
    try:
        parsed = parse_envelope(envelope)
    except EnvelopeParseError as exc:
        return GradeResult(False, 0.0, {"error": str(exc)})

    answer = parsed.get("answer")
    if not isinstance(answer, dict):
        return GradeResult(False, 0.0, {"error": "answer must be an object"})

    patch_text = answer.get("patch")
    if not isinstance(patch_text, str) or not patch_text.strip():
        return GradeResult(False, 0.0, {"error": "patch must be a non empty string"})

    success, patch_output = _apply_patch(patch_text, sandbox_path)
    if not success:
        return GradeResult(
            False,
            0.0,
            {"error": "patch failed", "patch_output": patch_output},
        )

    project_root = sandbox_path / "project"
    code, stdout, stderr = _run_pytest(project_root)

    passed = code == 0
    reward = 1.0 if passed else 0.0

    signals = {
        "pytest_stdout": stdout[-2000:],
        "pytest_stderr": stderr[-2000:],
    }

    return GradeResult(passed, reward, signals)


__all__ = ["grade"]
