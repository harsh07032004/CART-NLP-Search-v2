"""
Field-level accuracy benchmark for the NLP query parser.

Run from backend/:
    python eval/eval_parser.py

Each case in parser_benchmark.json lists only the fields it checks. A case
passes when every listed field matches exactly.
"""

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.query_parser import parse_query  # noqa: E402

CASES = json.loads((Path(__file__).parent / "parser_benchmark.json").read_text(encoding="utf-8"))


def main() -> int:
    fields_ok = fields_total = cases_ok = 0
    latencies = []
    failures = []

    for case in CASES:
        start = time.perf_counter()
        parsed = parse_query(case["q"])
        latencies.append((time.perf_counter() - start) * 1000)

        wrong = {k: (v, parsed.get(k)) for k, v in case["expect"].items() if parsed.get(k) != v}
        fields_total += len(case["expect"])
        fields_ok += len(case["expect"]) - len(wrong)
        if wrong:
            failures.append((case["q"], wrong))
        else:
            cases_ok += 1

    for q, wrong in failures:
        print(f"FAIL  {q!r}: " + ", ".join(f"{k} expected {e!r} got {g!r}" for k, (e, g) in wrong.items()))

    print(f"\nQueries          : {len(CASES)}")
    print(f"Field accuracy   : {fields_ok}/{fields_total} = {fields_ok / fields_total:.1%}")
    print(f"Exact-match rate : {cases_ok}/{len(CASES)} = {cases_ok / len(CASES):.1%}")
    print(f"Parse latency    : mean {statistics.mean(latencies):.2f} ms (includes cold cache)")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
