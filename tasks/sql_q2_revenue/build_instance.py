from __future__ import annotations

import csv
import random
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

_SANDBOX_BASE = Path(".tmp_sandbox")
_DATA_DIR = Path("data")

_VARIANTS: Dict[int, Dict[str, List[Dict[str, object]]]] = {
    1: {
        "products": [
            {"product_id": "W1", "category": "widgets"},
            {"product_id": "G1", "category": "gadgets"},
            {"product_id": "A1", "category": "accessories"},
        ],
        "orders": [
            {"order_id": "1001", "order_date": "2023-04-03", "product_id": "W1", "quantity": 2, "unit_price": 20.0},
            {"order_id": "1002", "order_date": "2023-04-20", "product_id": "G1", "quantity": 1, "unit_price": 45.0},
            {"order_id": "1003", "order_date": "2023-05-05", "product_id": "A1", "quantity": 5, "unit_price": 12.0},
            {"order_id": "1004", "order_date": "2023-06-15", "product_id": "W1", "quantity": 1, "unit_price": 20.0},
        ],
        "returns": [
            {"order_id": "1002"},
        ],
    },
    2: {
        "products": [
            {"product_id": "P1", "category": "hardware"},
            {"product_id": "P2", "category": "hardware"},
            {"product_id": "P3", "category": "software"},
        ],
        "orders": [
            {"order_id": "2001", "order_date": "2023-04-11", "product_id": "P1", "quantity": 1, "unit_price": 120.0},
            {"order_id": "2002", "order_date": "2023-05-19", "product_id": "P2", "quantity": 2, "unit_price": 90.0},
            {"order_id": "2003", "order_date": "2023-06-02", "product_id": "P3", "quantity": 3, "unit_price": 40.0},
        ],
        "returns": [],
    },
    3: {
        "products": [
            {"product_id": "C1", "category": "cloud"},
            {"product_id": "S1", "category": "support"},
        ],
        "orders": [
            {"order_id": "3001", "order_date": "2023-05-01", "product_id": "C1", "quantity": 10, "unit_price": 15.0},
            {"order_id": "3002", "order_date": "2023-05-15", "product_id": "S1", "quantity": 1, "unit_price": 200.0},
        ],
        "returns": [],
    },
}


def _render_layout(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        entries.append(f"- {path.relative_to(root).as_posix()}")
    return "\n".join(entries)


def _write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_readme(data_dir: Path) -> None:
    note = """Steps (copy into duckdb_sql):
CREATE OR REPLACE TABLE orders AS SELECT * FROM read_csv_auto('data/orders.csv');
CREATE OR REPLACE TABLE products AS SELECT * FROM read_csv_auto('data/products.csv');
CREATE OR REPLACE TABLE returns AS SELECT * FROM read_csv_auto('data/returns.csv');
SELECT p.category,
       ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.order_date BETWEEN '2023-04-01' AND '2023-06-30'
  AND o.order_id NOT IN (SELECT order_id FROM returns)
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 3;
"""
    (data_dir / "README.txt").write_text(note, encoding="utf-8")


def _compute_expected(variant_data: Dict[str, List[Dict[str, object]]]) -> List[Dict[str, float]]:
    products = {row["product_id"]: row["category"] for row in variant_data["products"]}
    returns = {row["order_id"] for row in variant_data["returns"]}
    revenue = defaultdict(float)

    for order in variant_data["orders"]:
        order_id = order["order_id"]
        if order_id in returns:
            continue
        order_date = order["order_date"]
        if not ("2023-04-01" <= order_date <= "2023-06-30"):
            continue
        category = products.get(order["product_id"])
        if not category:
            continue
        revenue[category] += float(order["quantity"]) * float(order["unit_price"])

    items = sorted(revenue.items(), key=lambda x: (-x[1], x[0]))[:3]
    return [
        {"category": category, "revenue": round(amount, 2)}
        for category, amount in items
    ]


def build_instance(run_id: str, base_tmp: Path | None = None) -> Dict[str, object]:
    base = base_tmp or _SANDBOX_BASE
    base.mkdir(parents=True, exist_ok=True)
    sandbox = base / f"run_{run_id}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    rng = random.Random(run_id)
    variant = rng.randint(1, len(_VARIANTS))
    data = _VARIANTS[variant]

    data_dir = sandbox / _DATA_DIR
    shutil.rmtree(data_dir, ignore_errors=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(data_dir / "products.csv", data["products"])
    _write_csv(data_dir / "orders.csv", data["orders"])
    _write_csv(data_dir / "returns.csv", data["returns"])
    _write_readme(data_dir)

    expected = _compute_expected(data)
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
