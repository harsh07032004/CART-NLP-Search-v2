import json
from pathlib import Path

import pytest

from app.utils.query_parser import parse_query

CASES = json.loads(
    (Path(__file__).resolve().parent.parent / "eval" / "parser_benchmark.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", CASES, ids=[c["q"] for c in CASES])
def test_benchmark_case(case):
    parsed = parse_query(case["q"])
    for field, expected in case["expect"].items():
        assert parsed[field] == expected, f"{field}: expected {expected!r}, got {parsed[field]!r}"


def test_price_text_does_not_leak_into_keywords():
    parsed = parse_query("nike shoes under 3000")
    assert "3000" not in parsed["keywords"]
    assert "under" not in parsed["keywords"]


def test_valid_words_are_never_corrected():
    # Regression: used to suggest "boots earphone in fastrack"
    assert parse_query("boat earphones in stock")["did_you_mean"] is None
    assert parse_query("kicks for men")["did_you_mean"] is None


def test_typo_gets_suggestion():
    assert parse_query("sheos for men")["did_you_mean"] == "shoes for men"


def test_brand_beats_fuzzy_category():
    # "boat" is a brand and must not be read as the category "boots"
    parsed = parse_query("boat earphones")
    assert parsed["brand"] == "boat"
    assert parsed["category"] == "earphone"
