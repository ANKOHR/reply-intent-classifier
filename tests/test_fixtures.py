import json
from reply_intent_classifier.fixtures import generate
from reply_intent_classifier.cli import read_inputs
from reply_intent_classifier.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / "replies.jsonl").read_text().startswith("# SYNTHETIC")
    assert all(r["synthetic"] is True for r in read_inputs(tmp_path))
    for name in ("expectations.json", "tiny.example.json"):
        assert json.loads((tmp_path / name).read_text())["synthetic"] is True

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    records = read_inputs(tmp_path)
    expected = json.loads((tmp_path / "expectations.json").read_text())
    planted = {label: sum(r["expected"] == label for r in records) for label in expected["counts"]}
    assert planted == expected["counts"]
    assert len(records) == expected["total"] == 200
    result = analyze(records)
    assert result["counts"] == planted
    assert result["evaluation"]["correct"] == 200

def test_corrupted_ground_truth_changes_report(tmp_path):
    generate(tmp_path)
    records = read_inputs(tmp_path)
    before = analyze(records)
    records[0]["expected"] = "negative"
    after = analyze(records)
    assert before["evaluation"]["errors"] == 0
    assert after["evaluation"]["errors"] == 1
    assert sum(after["evaluation"]["false_positives"].values()) == 1

def test_tiny_handwritten_input(tmp_path):
    generate(tmp_path)
    tiny = json.loads((tmp_path / "tiny.example.json").read_text())["records"]
    assert analyze(tiny)["evaluation"]["correct"] == 5
