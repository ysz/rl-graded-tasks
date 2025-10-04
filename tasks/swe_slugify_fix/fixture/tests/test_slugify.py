import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from slugify import slugify

CASES_PATH = Path(__file__).resolve().parents[1] / "data" / "cases.json"



def load_cases():
    if not CASES_PATH.exists():
        raise RuntimeError("cases.json missing in sandbox")
    with CASES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def ids_from_case(case):
    return case["title"]


@pytest.mark.parametrize("case", load_cases(), ids=ids_from_case)
def test_slugify_expected_output(case):
    assert slugify(case["input"]) == case["expected"]


@pytest.mark.parametrize("value", [None, 123, []])
def test_slugify_rejects_non_string(value):
    with pytest.raises(TypeError):
        slugify(value)
