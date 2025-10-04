import json
from copy import deepcopy
from pathlib import Path

import pytest

from merge import merge_dicts

CASES_PATH = Path(__file__).parent / "data" / "cases.json"


def load_cases():
    with CASES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def make_id(case):
    return case["title"]


@pytest.mark.parametrize("case", load_cases(), ids=make_id)
def test_merge_behavior(case):
    base = case["base"]
    patch = case["patch"]
    expected = case["expected"]

    base_copy = deepcopy(base)
    result = merge_dicts(base, patch)

    assert result == expected
    assert base == base_copy, "Base dictionary must not be mutated"


def test_type_guard():
    with pytest.raises(TypeError):
        merge_dicts({}, [])  # type: ignore[arg-type]
