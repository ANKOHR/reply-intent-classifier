"""Deterministic provenance-bearing report rendering."""
import json


def banner(result):
    p = result["provenance"]
    return (f"Data provenance: SYNTHETIC fixtures={p['synthetic']}; real Henry-entered records={p['real_henry_entered_declared']} (input declaration, not independently verified).")


def render(result, format="md"):
    if format == "json":
        return json.dumps({"banner": banner(result), **result}, ensure_ascii=False, indent=2, sort_keys=True).replace(chr(0x2014), "\\u2014") + "\n"
    e = result["evaluation"]
    lines = ["# Reply Intent Classifier", "", banner(result), "", result["honesty"], "",
             f"Total records: {result['total']}", f"Manual review required: {result['review_required']}", "", "| Intent | Count | Labelled false positives |", "| --- | ---: | ---: |"]
    for label, count in result["counts"].items():
        lines.append(f"| {label} | {count} | {e['false_positives'][label]} |")
    accuracy = "unmeasured (no supplied labels)" if e["accuracy"] is None else f"{e['accuracy']:.6f}"
    lines += ["", f"Supplied labels: {e['labelled']}; unlabelled: {e['unlabelled']}; correct: {e['correct']}; errors: {e['errors']}.", f"Accuracy against supplied labels: {accuracy}", "", "Per-record evidence and confusion matrix are available in the JSON report."]
    return "\n".join(lines) + "\n"
