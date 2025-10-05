from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from core.grading import GradeResult
from core.json_io import EnvelopeParseError, parse_envelope


def _apply_patch(patch_text: str, sandbox: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["patch", "-p0", "--batch", "--no-backup-if-mismatch"],
            input=patch_text,
            text=True,
            cwd=str(sandbox),
            capture_output=True,
            timeout=10,  # 10 second timeout for patch
        )
        success = proc.returncode == 0
        message = "\n".join(filter(None, [proc.stdout.strip(), proc.stderr.strip()]))
        return success, message
    except subprocess.TimeoutExpired:
        return False, "Patch command timed out after 10 seconds"


_PYTEST_TIMEOUT_SECONDS = 60


def _run_pytest(project_root: Path) -> tuple[int, str, str, bool]:
    import os
    try:
        # Prevent .pyc files and disable pytest cache to avoid conflicts
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            ["pytest", "-q", "-p", "no:cacheprovider"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=_PYTEST_TIMEOUT_SECONDS,
            env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return -1, stdout, stderr, True


def _parse_summary(stdout: str, fallback_total: int) -> tuple[int, int]:
    passed = 0
    failed = 0
    for line in stdout.splitlines():
        if "passed" in line or "failed" in line:
            tokens = line.replace(",", "").split()
            for idx, token in enumerate(tokens):
                if token.isdigit() and idx + 1 < len(tokens):
                    label = tokens[idx + 1]
                    if label == "passed":
                        passed = int(token)
                    elif label == "failed":
                        failed = int(token)
    if passed + failed == 0:
        failed = fallback_total
    return passed, failed


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

    ok, message = _apply_patch(patch_text, sandbox_path)
    if not ok:
        return GradeResult(False, 0.0, {"error": "patch failed", "patch_output": message})

    project_root = sandbox_path / "project"
    code, stdout, stderr, timed_out = _run_pytest(project_root)
    expected_cases = metadata.get("cases", [])
    passed, failed = _parse_summary(stdout, len(expected_cases))
    total = passed + failed if (passed + failed) else len(expected_cases)
    reward = passed / total if total else 0.0

    signals = {
        "pytest_stdout": stdout[-2000:],
        "pytest_stderr": stderr[-2000:],
        "passed_tests": passed,
        "failed_tests": failed,
        "variant": metadata.get("variant"),
        "pytest_timed_out": timed_out,
    }
    if timed_out:
        return GradeResult(False, 0.0, signals | {"error": "pytest timed out"})

    return GradeResult(code == 0, reward, signals)


__all__ = ["grade"]
