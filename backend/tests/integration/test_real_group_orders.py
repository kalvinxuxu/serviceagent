import json
from pathlib import Path

from evals.benchmark import load_cases


def test_real_group_order_suite_has_eight_business_cases():
    cases = load_cases("real_group_orders_v1")
    assert [case["id"] for case in cases] == [f"RG-{index:02d}" for index in range(1, 9)]
    assert all(case["expected"]["result_type"] in {"RESERVATION", "INVENTORY"} for case in cases)


def test_training_corpus_preserves_raw_role_and_timestamp_fields():
    path = Path(__file__).resolve().parents[3] / "data" / "training" / "real_group_orders_v1.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert {row["id"] for row in rows} >= {"RAW-20260821", "RAW-20260828"}
    assert all(message.get("role") in {"store", "customer"} and message.get("at") for row in rows for message in row["messages"])
