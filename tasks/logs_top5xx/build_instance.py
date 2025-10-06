from __future__ import annotations

import random
import shutil
from collections import Counter
from pathlib import Path
from typing import Dict, List

_SANDBOX_BASE = Path(".tmp_sandbox")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "access.log"

_LOG_TEMPLATE = (
    "{ip} - - [07/Jun/2023:12:00:00 +0000] \"GET {path} HTTP/1.1\" {status} {size} \"-\" \"{agent}\""
)

_VARIANTS: Dict[int, List[Dict[str, str]]] = {
    1: [
        {"ip": "10.0.0.1", "status": "500", "path": "/api", "agent": "Mozilla"},
        {"ip": "10.0.0.1", "status": "500", "path": "/api", "agent": "Mozilla"},
        {"ip": "10.0.0.2", "status": "502", "path": "/api", "agent": "Mozilla"},
        {"ip": "10.0.0.3", "status": "504", "path": "/login", "agent": "curl"},
        {"ip": "10.0.0.3", "status": "504", "path": "/login", "agent": "curl"},
        {"ip": "10.0.0.4", "status": "200", "path": "/health", "agent": "Mozilla"},
        {"ip": "10.0.0.5", "status": "503", "path": "/checkout", "agent": "status-bot"},
        {"ip": "10.0.0.6", "status": "500", "path": "/sync", "agent": "Mozilla"},
        {"ip": "10.0.0.7", "status": "200", "path": "/health", "agent": "Chrome"},
        {"ip": "10.0.0.8", "status": "200", "path": "/status", "agent": "Firefox"},
        {"ip": "10.0.0.1", "status": "200", "path": "/api", "agent": "Mozilla"},
        {"ip": "10.0.0.9", "status": "502", "path": "/sync", "agent": "Robot-Checker"},
        {"ip": "10.0.0.10", "status": "500", "path": "/data", "agent": "Safari"},
    ],
    2: [
        {"ip": "172.16.0.1", "status": "502", "path": "/", "agent": "Mozilla"},
        {"ip": "172.16.0.2", "status": "500", "path": "/export", "agent": "wget"},
        {"ip": "172.16.0.2", "status": "500", "path": "/export", "agent": "wget"},
        {"ip": "172.16.0.3", "status": "504", "path": "/login", "agent": "curl"},
        {"ip": "172.16.0.4", "status": "200", "path": "/dashboard", "agent": "Mozilla"},
        {"ip": "172.16.0.5", "status": "503", "path": "/status", "agent": "uptime-bot"},
        {"ip": "172.16.0.6", "status": "500", "path": "/", "agent": "Edge"},
        {"ip": "172.16.0.7", "status": "200", "path": "/api", "agent": "Chrome"},
        {"ip": "172.16.0.1", "status": "200", "path": "/", "agent": "Mozilla"},
        {"ip": "172.16.0.8", "status": "504", "path": "/login", "agent": "BOT-Monitor"},
        {"ip": "172.16.0.2", "status": "200", "path": "/export", "agent": "wget"},
    ],
    3: [
        {"ip": "192.168.1.10", "status": "500", "path": "/payments", "agent": "Mozilla"},
        {"ip": "192.168.1.10", "status": "500", "path": "/payments", "agent": "Mozilla"},
        {"ip": "192.168.1.11", "status": "503", "path": "/inventory", "agent": "curl"},
        {"ip": "192.168.1.12", "status": "504", "path": "/inventory", "agent": "Mozilla"},
        {"ip": "192.168.1.13", "status": "500", "path": "/inventory", "agent": "Mozilla"},
        {"ip": "192.168.1.14", "status": "200", "path": "/inventory", "agent": "Mozilla"},
        {"ip": "192.168.1.15", "status": "502", "path": "/checkout", "agent": "robotics-scanner"},
        {"ip": "192.168.1.16", "status": "200", "path": "/status", "agent": "Safari"},
        {"ip": "192.168.1.17", "status": "503", "path": "/api", "agent": "Chrome"},
        {"ip": "192.168.1.10", "status": "200", "path": "/payments", "agent": "Mozilla"},
        {"ip": "192.168.1.18", "status": "500", "path": "/data", "agent": "Firefox"},
    ],
    4: [
        {"ip": "10.1.1.1", "status": "503", "path": "/", "agent": "Chrome"},
        {"ip": "10.1.1.2", "status": "500", "path": "/", "agent": "SearchBot"},
        {"ip": "10.1.1.3", "status": "502", "path": "/", "agent": "Firefox"},
        {"ip": "10.1.1.3", "status": "502", "path": "/", "agent": "Firefox"},
        {"ip": "10.1.1.4", "status": "200", "path": "/", "agent": "Safari"},
        {"ip": "10.1.1.1", "status": "503", "path": "/", "agent": "Chrome"},
        {"ip": "10.1.1.5", "status": "504", "path": "/api", "agent": "Edge"},
        {"ip": "10.1.1.6", "status": "200", "path": "/api", "agent": "Opera"},
        {"ip": "10.1.1.7", "status": "500", "path": "/api", "agent": "monitoring-bot"},
        {"ip": "10.1.1.1", "status": "200", "path": "/api", "agent": "Chrome"},
        {"ip": "10.1.1.8", "status": "500", "path": "/sync", "agent": "Mozilla"},
        {"ip": "10.1.1.9", "status": "502", "path": "/data", "agent": "bOt-Crawler"},
        {"ip": "10.1.1.10", "status": "200", "path": "/health", "agent": "wget"},
        {"ip": "10.1.1.5", "status": "200", "path": "/api", "agent": "Edge"},
    ],
    5: [
        {"ip": "192.168.2.1", "status": "500", "path": "/app", "agent": "Bot-crawler"},
        {"ip": "192.168.2.2", "status": "502", "path": "/app", "agent": "Chrome"},
        {"ip": "192.168.2.3", "status": "504", "path": "/app", "agent": "Firefox"},
        {"ip": "192.168.2.3", "status": "504", "path": "/app", "agent": "Firefox"},
        {"ip": "192.168.2.4", "status": "200", "path": "/app", "agent": "Safari"},
        {"ip": "192.168.2.5", "status": "503", "path": "/app", "agent": "Opera"},
        {"ip": "192.168.2.2", "status": "502", "path": "/data", "agent": "Chrome"},
        {"ip": "192.168.2.6", "status": "500", "path": "/data", "agent": "FetchBot"},
        {"ip": "192.168.2.5", "status": "503", "path": "/data", "agent": "Opera"},
        {"ip": "192.168.2.7", "status": "500", "path": "/sync", "agent": "Edge"},
        {"ip": "192.168.2.8", "status": "200", "path": "/health", "agent": "curl"},
        {"ip": "192.168.2.9", "status": "504", "path": "/login", "agent": "Robotics-AI"},
        {"ip": "192.168.2.2", "status": "200", "path": "/app", "agent": "Chrome"},
    ],
    6: [
        {"ip": "172.20.0.10", "status": "500", "path": "/query", "agent": "Python-requests"},
        {"ip": "172.20.0.11", "status": "500", "path": "/query", "agent": "GoogleBot"},
        {"ip": "172.20.0.12", "status": "502", "path": "/query", "agent": "curl"},
        {"ip": "172.20.0.13", "status": "504", "path": "/query", "agent": "wget"},
        {"ip": "172.20.0.10", "status": "200", "path": "/query", "agent": "Python-requests"},
        {"ip": "172.20.0.10", "status": "500", "path": "/query", "agent": "Python-requests"},
        {"ip": "172.20.0.14", "status": "503", "path": "/query", "agent": "scraperbot"},
        {"ip": "172.20.0.15", "status": "500", "path": "/query", "agent": "Mozilla"},
        {"ip": "172.20.0.12", "status": "200", "path": "/query", "agent": "curl"},
        {"ip": "172.20.0.16", "status": "502", "path": "/api", "agent": "Safari"},
        {"ip": "172.20.0.17", "status": "200", "path": "/health", "agent": "Chrome"},
        {"ip": "172.20.0.18", "status": "500", "path": "/data", "agent": "boT-Scanner"},
        {"ip": "172.20.0.19", "status": "503", "path": "/sync", "agent": "Edge"},
    ],
    7: [
        {"ip": "10.2.2.1", "status": "500", "path": "/", "agent": "Mozilla"},
        {"ip": "10.2.2.1", "status": "500", "path": "/", "agent": "Mozilla"},
        {"ip": "10.2.2.2", "status": "502", "path": "/api", "agent": "Chrome"},
        {"ip": "10.2.2.3", "status": "200", "path": "/health", "agent": "Safari"},
        {"ip": "10.2.2.4", "status": "503", "path": "/sync", "agent": "ROBOT"},
        {"ip": "10.2.2.5", "status": "500", "path": "/data", "agent": "Firefox"},
        {"ip": "10.2.2.6", "status": "504", "path": "/login", "agent": "wget"},
        {"ip": "10.2.2.2", "status": "200", "path": "/api", "agent": "Chrome"},
        {"ip": "10.2.2.7", "status": "200", "path": "/status", "agent": "Edge"},
        {"ip": "10.2.2.1", "status": "200", "path": "/", "agent": "Mozilla"},
    ],
    8: [
        {"ip": "192.168.3.10", "status": "500", "path": "/checkout", "agent": "Safari"},
        {"ip": "192.168.3.11", "status": "502", "path": "/payments", "agent": "Chrome"},
        {"ip": "192.168.3.11", "status": "502", "path": "/payments", "agent": "Chrome"},
        {"ip": "192.168.3.12", "status": "504", "path": "/api", "agent": "automated-BOT"},
        {"ip": "192.168.3.13", "status": "200", "path": "/health", "agent": "Mozilla"},
        {"ip": "192.168.3.14", "status": "503", "path": "/inventory", "agent": "Edge"},
        {"ip": "192.168.3.10", "status": "500", "path": "/checkout", "agent": "Safari"},
        {"ip": "192.168.3.15", "status": "200", "path": "/status", "agent": "Firefox"},
        {"ip": "192.168.3.16", "status": "500", "path": "/sync", "agent": "curl"},
    ],
    9: [
        {"ip": "172.30.0.1", "status": "502", "path": "/", "agent": "Mozilla"},
        {"ip": "172.30.0.2", "status": "500", "path": "/export", "agent": "robotnik-crawler"},
        {"ip": "172.30.0.3", "status": "504", "path": "/query", "agent": "Chrome"},
        {"ip": "172.30.0.4", "status": "200", "path": "/health", "agent": "Safari"},
        {"ip": "172.30.0.1", "status": "502", "path": "/api", "agent": "Mozilla"},
        {"ip": "172.30.0.5", "status": "500", "path": "/data", "agent": "Firefox"},
        {"ip": "172.30.0.3", "status": "200", "path": "/query", "agent": "Chrome"},
        {"ip": "172.30.0.6", "status": "503", "path": "/login", "agent": "Edge"},
        {"ip": "172.30.0.7", "status": "200", "path": "/status", "agent": "wget"},
    ],
    10: [
        {"ip": "10.3.3.1", "status": "500", "path": "/api", "agent": "Chrome"},
        {"ip": "10.3.3.2", "status": "500", "path": "/api", "agent": "BotLike-Agent"},
        {"ip": "10.3.3.3", "status": "502", "path": "/sync", "agent": "Mozilla"},
        {"ip": "10.3.3.3", "status": "502", "path": "/sync", "agent": "Mozilla"},
        {"ip": "10.3.3.4", "status": "200", "path": "/health", "agent": "Safari"},
        {"ip": "10.3.3.5", "status": "503", "path": "/checkout", "agent": "Firefox"},
        {"ip": "10.3.3.1", "status": "200", "path": "/api", "agent": "Chrome"},
        {"ip": "10.3.3.6", "status": "504", "path": "/data", "agent": "Edge"},
        {"ip": "10.3.3.7", "status": "200", "path": "/status", "agent": "curl"},
        {"ip": "10.3.3.5", "status": "503", "path": "/inventory", "agent": "Firefox"},
    ],
}


def _render_layout(root: Path) -> str:
    return "\n".join(f"- {p.relative_to(root).as_posix()}" for p in sorted(root.rglob("*")) if p.is_file())


def _write_log(log_path: Path, entries: List[Dict[str, str]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        _LOG_TEMPLATE.format(
            ip=row["ip"],
            path=row["path"],
            status=row["status"],
            size="512",
            agent=row["agent"],
        )
        for row in entries
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_answer_key(root: Path, entries: List[Dict[str, str]]) -> None:
    instructions = """Python snippet to compute the answer:\nfrom collections import Counter\nfrom pathlib import Path\n\ncounts = Counter()\nfor line in Path('logs/access.log').read_text().splitlines():\n    parts = line.split()\n    status = parts[8] if len(parts) > 8 else ''\n    agent = line.split('"')[-2].lower() if '"' in line else ''\n    if not status.startswith('5') or 'bot' in agent:\n        continue\n    counts[parts[0]] += 1\nresult = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:5]\nprint(result)\n\nReturn the result as answer.results = [{"ip": ip, "count": count}]\n"""
    (root / "instructions.txt").write_text(instructions, encoding="utf-8")


def _compute_expected(entries: List[Dict[str, str]]) -> List[Dict[str, int]]:
    counter = Counter()
    for row in entries:
        if not row["status"].startswith("5"):
            continue
        if "bot" in row["agent"].lower():
            continue
        counter[row["ip"]] += 1
    items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return [{"ip": ip, "count": count} for ip, count in items[:5]]


def build_instance(run_id: str, base_tmp: Path | None = None) -> Dict[str, object]:
    base = base_tmp or _SANDBOX_BASE
    base.mkdir(parents=True, exist_ok=True)
    sandbox = base / f"run_{run_id}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    rng = random.Random(run_id)
    variant = rng.randint(1, len(_VARIANTS))
    entries = _VARIANTS[variant]

    log_path = sandbox / LOG_FILE
    _write_log(log_path, entries)
    _write_answer_key(sandbox, entries)

    expected = _compute_expected(entries)
    layout_hint = _render_layout(sandbox)

    return {
        "sandbox_path": sandbox,
        "prompt_vars": {"layout_hint": layout_hint, "variant": variant},
        "metadata": {
            "variant": variant,
            "expected": expected,
        },
    }


__all__ = ["build_instance"]
