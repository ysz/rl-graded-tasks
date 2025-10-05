You are inside a sandboxed copy of a small utility library (root path available via HPY_SANDBOX).

Task: Fix project/merge/merge.py so merge_dicts returns a brand new dictionary that recursively merges nested dicts without mutating the base argument.

The current implementation has a bug where nested dictionary references might be shared between input and output, causing mutations. The issue is in how the base dictionary is copied before merging.

Required format:
{{"passed": false, "answer": {{"patch": "--- project/merge/merge.py\n+++ project/merge/merge.py\n@@ ...your patch here..."}}}}

Notes:
- Read project/merge/merge.py to understand the current implementation
- You will need to fix how dictionaries are copied in the merge process
- Consider what happens with nested dictionary structures
- Patch format must work with patch -p0 (no a/ b/ prefixes)
- Include enough context lines so patch can apply cleanly

Sandbox snapshot:
{layout_hint}
