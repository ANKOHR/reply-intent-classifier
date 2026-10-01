"""Synthetic planted examples; no random generation, no seed needed."""
import json
from pathlib import Path

EXAMPLES = {
    "positive": ("Interested in learning more.", "Please book a call.", "Sounds good, send details.", "Let's talk tomorrow."),
    "negative": ("Not interested, thanks.", "No thanks.", "Please remove me.", "Unsubscribe from this list."),
    "objection": ("This is too expensive.", "We have no budget.", "We already use another solution.", "I need approval first."),
    "timing": ("Try next quarter.", "Check back next month.", "Not right now.", "Later this year would work."),
    "referral": ("Contact my colleague Alex.", "Speak to Sam about this.", "Reach out to our CTO.", "I forwarded to the team."),
}

def generate(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for label, examples in EXAMPLES.items():
        for number in range(40):
            records.append({"id": f"{label}-{number:03}", "text": examples[number % 4] + f" Reference {number}.", "synthetic": True, "expected": label})
    (directory / "replies.jsonl").write_text("# SYNTHETIC: planted phrase examples, not real trial evidence.\n" + "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    # Hand computed: five groups of 40, ten repetitions of four examples.
    expectations = {"synthetic": True, "comment": "SYNTHETIC: hand-computed expectations, not classifier output", "total": 200,
                    "counts": {"positive": 40, "negative": 40, "objection": 40, "timing": 40, "referral": 40, "unclassified": 0},
                    "labelled": 200, "correct": 200, "errors": 0, "false_positives": 0}
    (directory / "expectations.json").write_text(json.dumps(expectations, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tiny = [{"id": "tiny-" + label, "text": examples[0], "synthetic": True, "expected": label} for label, examples in EXAMPLES.items()]
    (directory / "tiny.example.json").write_text(json.dumps({"synthetic": True, "comment": "SYNTHETIC: five hand-written records; copy into a separate input directory", "records": tiny}, indent=2) + "\n", encoding="utf-8")
