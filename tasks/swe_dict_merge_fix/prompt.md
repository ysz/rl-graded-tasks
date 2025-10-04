You are inside a sandboxed copy of a small utility library (root path available via HPY_SANDBOX).

Task: update project/merge/merge.py so that merge_dicts returns a brand new dictionary, performs a recursive merge on nested dicts, and copies primitives from patch without mutating base. Follow this recipe:
- Start by copying base (e.g. using dict(base) or copy.deepcopy).
- For each key in patch: if both sides are dicts, merge them recursively; otherwise replace the value.
- Return the cloned result.
Run pytest once your changes are in place and submit the diff only when it passes.

Guidance:
- Study project/tests/data/cases.json for the scenarios that must pass.
- Modify project/merge/merge.py in place with a minimal diff.
- Use the provided tools (file_read, file_write, run_pytests) to inspect the code and run the test suite.
- When the tests succeed, submit a JSON envelope containing the unified diff under answer.patch. Leave passed=false if you are unsure.

Sandbox snapshot:
{layout_hint}
