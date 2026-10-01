"""Pure phrase classification and measured label comparison."""
import re
from datetime import date

LABELS = ("positive", "negative", "objection", "timing", "referral")
# Priority makes conflicting explicit signals reproducible. Unknown text is abstained.
RULES = {
    "negative": ("not interested", "no thanks", "remove me", "unsubscribe", "do not contact", "don't contact"),
    "referral": ("contact my colleague", "speak to", "reach out to", "forwarded to", "contact instead"),
    "timing": ("next quarter", "next month", "later this year", "not right now", "check back", "after january"),
    "objection": ("too expensive", "no budget", "already use", "already have", "security concerns", "need approval"),
    "positive": ("interested", "book a call", "schedule a call", "send details", "sounds good", "let's talk"),
}
AS_OF = "2026-09-30"
MAX_TEXT = 100000

class InputError(ValueError):
    """Named validation or parse failure."""


def classify(text):
    """Return an auditable phrase match, not a prediction of human intent."""
    normalized = " ".join(text.casefold().replace("’", "'").split())
    matches = []
    for label, phrases in RULES.items():
        for phrase in phrases:
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", normalized):
                matches.append({"label": label, "phrase": phrase})
    labels = {m["label"] for m in matches}
    # Negative wins for opt-outs. Multiple other intents need manual review.
    label = "negative" if "negative" in labels else next(iter(labels)) if len(labels) == 1 else "unclassified"
    return {"label": label, "matches": matches, "review_required": label == "unclassified" or len(labels) > 1}


def validate(record, as_of=AS_OF):
    allowed = {"id", "text", "synthetic", "expected", "received_at", "source"}
    if not isinstance(record, dict):
        raise InputError("SchemaError: record must be an object")
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise InputError("SchemaError: unknown field(s): " + ", ".join(unknown))
    for field in ("id", "text", "synthetic"):
        if field not in record:
            raise InputError("SchemaError: missing field " + field)
    if not isinstance(record["id"], str) or not record["id"].strip() or len(record["id"]) > 200:
        raise InputError("SchemaError: id must be a nonempty string of at most 200 characters")
    if not isinstance(record["text"], str) or len(record["text"]) > MAX_TEXT:
        raise InputError("SchemaError: text must be a string of at most 100000 characters")
    if type(record["synthetic"]) is not bool:
        raise InputError("SchemaError: synthetic must be true or false")
    if not record["synthetic"] and record.get("source") != "henry_entered":
        raise InputError("SchemaError: real source must be henry_entered (user declaration)")
    if "expected" in record and record["expected"] not in LABELS + ("unclassified",):
        raise InputError("SchemaError: expected has an unsupported label")
    if "received_at" in record:
        try:
            received = date.fromisoformat(record["received_at"])
            cutoff = date.fromisoformat(as_of)
        except (ValueError, TypeError):
            raise InputError("SchemaError: received_at and as_of must be ISO dates") from None
        if received > cutoff:
            raise InputError("SchemaError: received_at is after as_of " + as_of)
    return record


def analyze(records, as_of=AS_OF):
    counts = dict.fromkeys(LABELS + ("unclassified",), 0)
    matrix = {label: dict.fromkeys(counts, 0) for label in counts}
    seen, rows = set(), []
    correct = labelled = synthetic = review = 0
    for record in records:
        validate(record, as_of)
        if record["id"] in seen:
            raise InputError("SchemaError: duplicate id " + record["id"])
        seen.add(record["id"])
        result = classify(record["text"])
        counts[result["label"]] += 1
        synthetic += record["synthetic"]
        review += result["review_required"]
        if "expected" in record:
            labelled += 1
            correct += record["expected"] == result["label"]
            matrix[record["expected"]][result["label"]] += 1
        rows.append({**record, **result})
    rows.sort(key=lambda row: row["id"])
    false_positives = {label: sum(matrix[actual][label] for actual in matrix if actual != label) for label in counts}
    return {"schema_version": 1, "as_of": as_of, "total": len(rows), "counts": counts,
            "provenance": {"synthetic": synthetic, "real_henry_entered_declared": len(rows) - synthetic},
            "evaluation": {"labelled": labelled, "unlabelled": len(rows) - labelled, "correct": correct,
                           "errors": labelled - correct, "accuracy": correct / labelled if labelled else None,
                           "false_positives": false_positives, "confusion_matrix": matrix},
            "review_required": review, "records": rows,
            "honesty": "Phrase matches computed from supplied text. Accuracy measured only against supplied labels; not independent validation. Time and money savings unmeasured and not reported."}
