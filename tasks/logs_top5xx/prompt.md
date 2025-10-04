You are inspecting HTTP access logs provided in the sandbox (HPY_SANDBOX). Identify the top five client IPs that triggered 5xx responses. Sort the result by count descending, then IP ascending. Exclude any line whose user-agent contains the word "bot" (case insensitive).
Steps that work well:
1) Read logs/access.log with file_read.
2) Use python_expression with a short script that splits each line, filters status codes starting with "5", skips lines whose agent contains "bot", and counts using collections.Counter.
3) Sort the Counter items by (-count, ip) and slice the first five.
Return the JSON envelope with results. A template is below.

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
- The log file lives under logs/access.log.
- Status code is in the ninth field of the combined log format.
- Remove any entry where the agent string matches /bot/i before reporting.

Sandbox map:
{layout_hint}
