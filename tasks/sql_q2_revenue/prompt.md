You have a DuckDB sandbox with small CSV files under data/. Compute the top three product categories by net revenue in Q2 2023 (April 1 through June 30, inclusive). Revenue is quantity * unit_price. Exclude any orders listed in returns.csv. Return revenue rounded to two decimal places.
Suggested workflow:
1) Register the CSVs: use duckdb_sql("CREATE OR REPLACE TABLE orders AS SELECT * FROM read_csv_auto('data/orders.csv')") and similar for products and returns.
2) Run a query with WHERE order_date BETWEEN "2023-04-01" AND "2023-06-30" AND order_id NOT IN (SELECT order_id FROM returns).
3) SUM(quantity * unit_price) grouped by products.category, ORDER BY revenue DESC, LIMIT 3.
Return the rounded results in the JSON envelope.

Submit the unified envelope:
{{
  "passed": false,
  "checks": {{}},
  "answer": {{"results": [{{"category": "widgets", "revenue": 123.45}}]}},
  "notes": "optional"
}}

Available tools:
- duckdb_sql(query)
- file_read(path)
- python_expression(expression)
- submit_answer(answer)

Hints:
- The CSV files are loaded from the sandbox root; use absolute or HPY_SANDBOX-relative paths in DuckDB.
- You may register the CSVs as temporary tables before querying.

Sandbox file list:
{layout_hint}
