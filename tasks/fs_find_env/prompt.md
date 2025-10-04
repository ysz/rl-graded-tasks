You are inspecting a small repository snapshot inside a sandbox. The root path is stored in the HPY_SANDBOX environment variable.

Task: find every file whose name starts with ".env" that contains at least one uncommented line beginning with "SECRET=". Ignore any matches under the tests/ directory. Each match must be returned as a relative path from the sandbox root.

Available tools:
- glob_find(pattern, exclude)
- grep_search(pattern, path, flags)
- file_read(path)
- submit_answer(answer)

Hints:
- Use glob_find to list ".env*" files. Exclude tests/** explicitly.
- Use grep_search with a regex like "^SECRET=" and ignore_case false.
- Use file_read to double check tricky files if grep output is ambiguous.
- Sort the final list of paths in lexicographic order.

When you are done, call submit_answer with a JSON envelope:
{{
  "passed": false,
  "checks": {{}},
  "answer": {{"paths": ["relative/path"]}},
  "notes": "optional"
}}

Set "passed" to true only if you are fully confident. Leave it false otherwise. Always include the "answer" object. Do not add extra fields.

Sandbox layout preview:
{layout_hint}
