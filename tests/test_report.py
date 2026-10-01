import json
from reply_intent_classifier.core import analyze
from reply_intent_classifier.report import render
from reply_intent_classifier.fixtures import generate
from reply_intent_classifier.cli import read_inputs

def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    result = json.loads(render(analyze(read_inputs(tmp_path)), "json"))
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert result["total"] == expected["total"]
    assert result["counts"] == expected["counts"]
    for key in ("labelled", "correct", "errors"):
        assert result["evaluation"][key] == expected[key]
    assert sum(result["counts"].values()) == result["total"]

def test_report_zero_false_positives(tmp_path):
    generate(tmp_path)
    assert sum(analyze(read_inputs(tmp_path))["evaluation"]["false_positives"].values()) == 0

def test_report_carries_provenance_banner():
    for format in ("md", "json"):
        output = render(analyze([]), format)
        assert "Data provenance:" in output and "SYNTHETIC" in output and "Henry-entered" in output

def test_hypothetical_figures_labelled():
    output = render(analyze([]))
    assert "Time and money savings unmeasured and not reported" in output
    assert "Accuracy against supplied labels: unmeasured" in output

def test_no_em_dashes_in_outputs():
    result = analyze([{"id": "a", "text": "Interested" + chr(0x2014), "synthetic": True}])
    for format in ("md", "json"):
        assert chr(0x2014) not in render(result, format)
    assert json.loads(render(result, "json"))["records"][0]["text"].endswith(chr(0x2014))
