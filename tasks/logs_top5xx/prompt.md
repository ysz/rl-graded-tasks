You are inspecting HTTP access logs provided in the sandbox (HPY_SANDBOX). Identify the top five client IPs that triggered 5xx responses. Sort the result by count descending, then IP ascending. Exclude any line whose user-agent contains the word "bot" (case insensitive).


Return the answer in the JSON envelope with:
{{
  "passed": false,
  "checks": {{}},
  "answer": {{"results": [{{"ip": "1.2.3.4", "count": 3}}]}},
  "notes": "optional"
}}

Available tools:
- file_read(path)
- grep_search(pattern, path, flags)
- python_expression(expression)
- submit_answer(answer)

Hints:
- Log file: logs/access.log
- python_expression: no imports, built-in functions only
- Examine the log format to extract relevant fields

Sandbox map:
{layout_hint}
