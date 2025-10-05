You are inspecting a small repository snapshot inside a sandbox. The root path is stored in the HPY_SANDBOX environment variable.

Task: find every file whose name starts with ".env" that contains at least one uncommented line beginning with "SECRET=". Ignore any matches under the tests/ directory. Return the matches as relative paths from the sandbox root, sorted in lexicographic order.

Available tools:
- glob_find(pattern, exclude)
- grep_search(pattern, path, flags)
- file_read(path)
- submit_answer(answer)

Step by step approach:
1. Use glob_find to list ".env*" files. Exclude tests/** explicitly.
2. For each file found, use grep_search with the EXACT regex pattern "^SECRET=" to find lines that:
   - Start at the beginning of the line (no leading spaces, no prefixes like "export ")
   - Have "SECRET=" immediately at the start
   - Lines starting with "#" are comments and will NOT match this pattern
   - Lines with " SECRET=" (leading space) will NOT match
   - Lines with "export SECRET=" will NOT match
3. ONLY include files where grep_search returns at least one match in the "matches" array.
4. Sort the matching file paths in lexicographic order.
5. Call submit_answer with your answer.

IMPORTANT: You must call submit_answer before running out of steps. Do not forget this final step.

When you are done, call submit_answer with a JSON envelope:
{{
  "passed": false,
  "checks": {{}},
  "answer": {{"paths": ["path1", "path2"]}},
  "notes": "optional"
}}

Example: If you find .env and config/.env.prod that contain SECRET=, your answer should be:
{{
  "passed": true,
  "checks": {{}},
  "answer": {{"paths": [".env", "config/.env.prod"]}},
  "notes": ""
}}

Set "passed" to true if you are confident in your answer. Always include the "answer" object with "paths" array. Do not add extra fields.

Sandbox layout preview:
{layout_hint}
