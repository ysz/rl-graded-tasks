from __future__ import annotations

import os
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterable, List

import duckdb

SANDBOX_ENV_VAR = "HPY_SANDBOX"
_MAX_IO_CHARS = 2000


class SandboxError(RuntimeError):
    """Raised when a tool attempts to leave the sandbox or sandbox is missing."""


def _get_sandbox_root() -> Path:
    raw = os.environ.get(SANDBOX_ENV_VAR)
    if not raw:
        raise SandboxError("Sandbox path is not configured")
    root = Path(raw).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SandboxError("Sandbox path does not exist")
    return root


def _normalize_user_path(path: str, sandbox: Path) -> str:
    """Convert user supplied paths to sandbox relative ones."""

    if not isinstance(path, str):
        raise SandboxError("Path must be a string")

    candidate = path.strip()
    if not candidate:
        return ""

    candidate = candidate.replace("\\", "/")
    for marker in ("{HPY_SANDBOX}", "$HPY_SANDBOX", "${HPY_SANDBOX}"):
        candidate = candidate.replace(marker, "")

    sandbox_prefix = sandbox.as_posix()
    if candidate.startswith(sandbox_prefix):
        candidate = candidate[len(sandbox_prefix) :]

    candidate = candidate.lstrip("/")
    while candidate.startswith("./"):
        candidate = candidate[2:]

    parts = Path(candidate).parts
    if any(part == ".." for part in parts):
        raise SandboxError("Path escapes sandbox")

    return candidate


def _resolve_in_sandbox(path: str | os.PathLike[str], sandbox: Path) -> Path:
    candidate = (sandbox / Path(path)).resolve()
    if sandbox not in candidate.parents and candidate != sandbox:
        raise SandboxError("Path escapes sandbox")
    return candidate


def _trim_text(text: str, limit: int = _MAX_IO_CHARS) -> str:
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return text[:head] + "\n...\n" + text[-tail:]


def file_read(path: str) -> Dict[str, Any]:
    sandbox = _get_sandbox_root()
    normalized = _normalize_user_path(path, sandbox)
    target = _resolve_in_sandbox(normalized or ".", sandbox)
    if not target.exists() or not target.is_file():
        raise SandboxError("File not found inside sandbox")
    content = target.read_text()
    return {"content": _trim_text(content)}


def file_write(path: str, content: str) -> Dict[str, Any]:
    sandbox = _get_sandbox_root()
    normalized = _normalize_user_path(path, sandbox)
    target = _resolve_in_sandbox(normalized or ".", sandbox)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return {"ok": True}


def run_pytests() -> Dict[str, Any]:
    sandbox = _get_sandbox_root()
    # Set PYTHONDONTWRITEBYTECODE to prevent .pyc file creation
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        ["pytest", "-q", "-p", "no:cacheprovider"],
        cwd=str(sandbox),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return {
        "returncode": int(proc.returncode),
        "stdout": _trim_text(proc.stdout),
        "stderr": _trim_text(proc.stderr),
    }


def _iter_files_with_glob(pattern: str, sandbox: Path) -> List[Path]:
    matches: List[Path] = []
    for candidate in sandbox.glob(pattern or "*"):
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        parents = list(resolved.parents)
        if resolved == sandbox or sandbox in parents:
            matches.append(resolved)
    return matches


def glob_find(pattern: str, exclude: Iterable[str] | None = None) -> Dict[str, Any]:
    sandbox = _get_sandbox_root()
    normalized_pattern = _normalize_user_path(pattern, sandbox)
    matches: List[str] = []
    exclusion = list(exclude or [])
    for path in sandbox.rglob(normalized_pattern or "*"):
        if not path.is_file():
            continue
        rel = path.relative_to(sandbox).as_posix()
        if any(fnmatch(rel, rule) for rule in exclusion):
            continue
        matches.append(rel)
    matches.sort()
    return {"paths": matches}


def grep_search(pattern: str, path: str, flags: Dict[str, Any] | None = None) -> Dict[str, Any]:
    sandbox = _get_sandbox_root()
    normalized = _normalize_user_path(path, sandbox)
    options = flags or {}
    re_flags = 0
    if options.get("ignore_case"):
        re_flags |= re.IGNORECASE
    if options.get("multiline"):
        re_flags |= re.MULTILINE
    if options.get("dotall"):
        re_flags |= re.DOTALL
    compiled = re.compile(pattern, re_flags)

    has_glob = any(ch in normalized for ch in "*?[") or "**" in normalized
    if has_glob:
        search_paths = _iter_files_with_glob(normalized, sandbox)
    else:
        target = _resolve_in_sandbox(normalized or ".", sandbox)
        if target.is_dir():
            search_paths = [p for p in target.rglob("*") if p.is_file()]
        elif target.exists():
            search_paths = [target]
        else:
            return {"matches": []}

    results = []
    for file_path in search_paths:
        try:
            text = file_path.read_text()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        rel = file_path.relative_to(sandbox).as_posix()
        for idx, line in enumerate(text.splitlines(), start=1):
            if compiled.search(line):
                results.append({"file": rel, "line": idx, "text": line[:256]})
    return {"matches": results}


def duckdb_sql(query: str) -> Dict[str, Any]:
    sandbox = _get_sandbox_root()
    con = duckdb.connect(database=":memory:")
    try:
        con.execute(f"SET temp_directory='{sandbox.as_posix()}';")
        results = con.execute(query).fetchdf()
    finally:
        con.close()
    columns = list(results.columns)
    rows = results.values.tolist()
    return {"columns": columns, "rows": rows}


TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "file_read": {
        "name": "file_read",
        "description": "Read a text file from the sandbox",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    "file_write": {
        "name": "file_write",
        "description": "Write content to a sandbox file, creating parent folders if needed",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    "run_pytests": {
        "name": "run_pytests",
        "description": "Execute pytest within the sandbox",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    "glob_find": {
        "name": "glob_find",
        "description": "Run a glob search relative to the sandbox root",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "exclude": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                },
            },
            "required": ["pattern"],
        },
    },
    "grep_search": {
        "name": "grep_search",
        "description": "Search for lines matching a regex within a file or folder",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "flags": {
                    "type": "object",
                    "properties": {
                        "ignore_case": {"type": "boolean"},
                        "multiline": {"type": "boolean"},
                        "dotall": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                    "default": {},
                },
            },
            "required": ["pattern", "path"],
        },
    },
    "duckdb_sql": {
        "name": "duckdb_sql",
        "description": "Execute a DuckDB query using data in the sandbox",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
}


TOOL_HANDLERS = {
    "file_read": file_read,
    "file_write": file_write,
    "run_pytests": run_pytests,
    "glob_find": glob_find,
    "grep_search": grep_search,
    "duckdb_sql": duckdb_sql,
}


__all__ = [
    "SANDBOX_ENV_VAR",
    "TOOL_HANDLERS",
    "TOOL_SPECS",
    "SandboxError",
    "duckdb_sql",
    "file_read",
    "file_write",
    "glob_find",
    "grep_search",
    "run_pytests",
]
