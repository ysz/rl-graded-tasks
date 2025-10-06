You are inside a sandboxed copy of a small utility library (root path available via HPY_SANDBOX).

Task: Fix project/merge/merge.py so merge_dicts returns a brand new dictionary that recursively merges nested dicts without mutating the base argument.

The current implementation has a bug where nested dictionary references might be shared between input and output, causing mutations. The issue is in how the base dictionary is copied before merging.

Required format:
{{"passed": false, "answer": {{"patch": "--- project/merge/merge.py\n+++ project/merge/merge.py\n@@ ...your patch here..."}}}}

Constraints:
- DO NOT import any new modules (including copy, deepcopy, or similar)
- The fix must use only built-in dict operations and recursion
- All existing imports must remain unchanged

Notes:
- Read project/merge/merge.py to understand the current implementation
- You will need to manually handle deep copying of nested structures
- The solution requires careful handling of both dict and non-dict values
- Patch format must work with patch -p0 (no a/ b/ prefixes)
- Include enough context lines so patch can apply cleanly
- The key insight: use recursion to copy nested dictionaries

Sandbox snapshot:
{layout_hint}
