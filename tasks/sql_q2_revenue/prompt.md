You have a DuckDB sandbox with CSV files under data/: orders.csv, products.csv, and returns.csv.

Task: Compute the top three product categories by net revenue in Q2 2023 (April 1 through June 30, inclusive).

Requirements:
- Revenue = quantity * unit_price
- Exclude any orders in returns.csv
- Round revenue to two decimal places
- Order by revenue descending

Answer format: {{"passed": false, "checks": {{}}, "answer": {{"results": [category, revenue objects]}}, "notes": ""}}

Tools: duckdb_sql, file_read, python_expression, submit_answer

Sandbox files:
{layout_hint}
