import pytest
from reply_intent_classifier.core import analyze, classify, InputError

def row(**updates):
    return {"id": "a", "text": "Interested", "synthetic": True, **updates}

@pytest.mark.parametrize("text,label", [("Not interested", "negative"), ("Interested", "positive"), ("Next quarter", "timing"), ("No budget", "objection"), ("Speak to Alex", "referral"), ("Interesting", "unclassified"), ("Interested but no budget", "unclassified"), ("Not interested, next quarter", "negative"), ("I am not sure", "unclassified")])
def test_classification(text, label):
    assert classify(text)["label"] == label

@pytest.mark.parametrize("updates", [{"amount": -1}, {"received_at": "2099-01-01"}, {"text": "x" * 100001}, {"id": ""}, {"synthetic": "true"}, {"expected": "wrong"}, {"synthetic": False}, {"received_at": "invalid"}])
def test_rejects_adversarial_values(updates):
    with pytest.raises(InputError):
        analyze([row(**updates)])

def test_duplicate_ids():
    with pytest.raises(InputError, match="duplicate id"):
        analyze([row(), row()])

def test_handles_unicode_and_long_inputs():
    result = analyze([row(text="你好 café C:\\Users\\henry " + "x" * 90000 + " interested")])
    assert result["counts"]["positive"] == 1

def test_real_declaration():
    result = analyze([row(synthetic=False, source="henry_entered")])
    assert result["provenance"]["real_henry_entered_declared"] == 1
