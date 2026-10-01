# Reply Intent Classifier

`ric` computes transparent phrase matches for positive, negative, objection, timing and referral replies. It is a CPU-only Python CLI with no runtime dependencies, network access, model calls or database. Ambiguous and unmatched replies become `unclassified` for human review.

Hypothesis: explicit rules can give Henry a reproducible, auditable first pass for technical outbound replies. Acceptance: the planted 200-record synthetic fixture yields all 200 supplied labels correctly, zero labelled false positives, reconciled counts and a complete demo in under five seconds. This fixture establishes rule correctness, not real-world accuracy or demand.

## Quickstart

Python 3.10 or newer and an existing setuptools installation are needed. Install locally without contacting an index:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
ric fixtures --out demo
ric run --input demo
ric report --format md
python -m pytest -q
```

If the user Scripts directory is absent from PATH, use `python -m reply_intent_classifier.cli` in place of `ric`, or install into a virtual environment and activate it. Pytest is a development requirement, not a runtime dependency. No dependencies are downloaded by the above install command.

For the smallest version, copy `fixtures/synthetic/tiny.example.json` into a new input directory as `replies.json`, then run and report on that directory. It contains five hand-written synthetic replies. The main demo generates 200 records.

## Input reference

Input directories contain UTF-8 `.json`, `.jsonl` or `.csv` files. Files are sorted by filename; records are sorted by id in output. JSON is an array of records or an object with a `records` array. JSONL permits blank lines and header comments starting with `#`. CSV has a header and uses standard quoting, including quoted multiline text. JSON escaping preserves Windows paths. YAML is intentionally unsupported and produces a named schema error with file and line, without a traceback.

Illustrative SYNTHETIC record:

```json
{"id":"example-1","text":"Please book a call","synthetic":true,"expected":"positive"}
```

| Field | Rule |
| --- | --- |
| id | Required unique nonempty string, at most 200 characters, unique across files |
| text | Required string, at most 100000 characters; empty text is unclassified |
| synthetic | Required JSON boolean; CSV uses exactly `true` or `false` |
| expected | Optional hand-checked label: one of five intents or unclassified |
| source | For real records, required exact value `henry_entered`, declared by Henry |
| received_at | Optional ISO date; must be on or before `--as-of` |

Use `synthetic:false` and `source:henry_entered` only for Henry's own data entered by him. This is a declaration, not verification of identity or origin. Omit `expected` until a person has hand-checked the reply. Do not put real trials in git. Generated output and demo directories are ignored; store other real input directories outside the repo.

Unknown fields are rejected, including `amount` and negative amounts: this tool has no financial domain. Future dates are rejected against the explicit cutoff. The default cutoff is fixed at 2026-09-30 for deterministic results; pass `--as-of 2026-10-01` or another intended date for later trials. Duplicate ids, malformed dates and oversized strings are errors, never silently dropped. Input parse failures include filename and physical line. JSON schema errors report line 1 (the document) and offending field; JSONL and CSV schema errors use the record line. UTF-8 errors name the file and document line 1.

`expectations.json` and `tiny.example.json` are reserved fixture metadata names and ignored by the input loader. Hidden files are ignored. All other unsupported files fail explicitly. The optional synthetic field on a JSON envelope documents the fixture; each record still needs its own provenance declaration.

## Commands

| Command | Purpose and example |
| --- | --- |
| fixtures | `ric fixtures --out demo`: writes the labelled 200-record fixture and expectations |
| run | `ric run --input demo --state .ric/results.json`: validates, computes and atomically saves results |
| report | `ric report --format json --out report.json`: recomputes from saved records and renders evidence |
| classify | `ric classify --text "No thanks"`: explains one illustrative synthetic phrase example |
| audit | `ric audit --input demo`: computes JSON evidence against any supplied labels without saving state |

Every command has `--help` and an example. `run` and `audit` accept `--as-of`. `report` accepts `--state`, `--format md|json`, and optional `--out`. Exit code 0 means successful execution, not agreement with all supplied labels. Invalid input or output paths return 2 and a named error. Argparse usage errors also return 2. A previous successful state remains intact after a failed run. Reports replace their destination atomically; failed writes remove temporary files and preserve existing files.

## Architecture

```text
local JSON / JSONL / CSV -> CLI validation -> pure core phrase rules
                                             |
synthetic generator -> planted labels -> counts + per-record match evidence
                                             |
                                  atomic local results JSON
                                             |
                              recompute -> Markdown / JSON report
```

Rules normalize case, whitespace and curly apostrophes, then match complete phrases with word boundaries. `core.py` lists every supported phrase. Negative opt-outs take precedence over other matches. Multiple distinct nonnegative intents are unclassified. Multiple intents, unmatched text and ambiguous text require manual review. A single label without review does not establish true intent. No probabilistic confidence is invented. No random seed is needed because no randomness is used.

## Honesty boundary and fixture policy

Reports explicitly count synthetic and declared real records, including mixed sets. Each fixture file has a synthetic header comment or JSON `comment` field and `synthetic:true`; each record has `synthetic:true`. Fixtures are 40 planted records per intent, built from four phrases repeated ten times with reference numbers. Expectations are independently specified by the arithmetic 5 x 40 = 200, not copied from classifier results. Their success is deliberately narrow evidence.

Counts come from classifications. Labelled accuracy is correct supplied labels divided by supplied labels; unlabelled records are excluded. With no labels, accuracy is null in JSON and unmeasured in Markdown. False positives for an intent count labelled records whose prediction is that intent and whose supplied label differs. They are not claims about unlabelled records. JSON includes the full confusion matrix, input text, expected labels and matched phrases. Corrupting a label changes evaluation figures while leaving text-derived intent counts intact.

Illustrative text passed to `classify` is labelled synthetic. Time and money savings are unmeasured and not reported. No savings baseline exists. Demo duration in `EVIDENCE.md` is an observed local elapsed time, not savings. Runtime results contain no timestamps so identical inputs, rules and options produce byte-identical output. Literal em dash characters from input are preserved as JSON Unicode escapes so outputs contain no literal em dashes.

## Failure modes and limitations

Named errors cover missing input with a usage hint, malformed input, schema drift with offending fields, and output write failure. No partial report files remain after a write failure. Text may include sarcasm, negation, quoted previous messages or signatures containing rule phrases. Rules do not understand these structures. For example, an isolated phrase inside a quotation can be falsely classified, and unsupported paraphrases are unclassified. Non-English text is preserved but generally unmatched. Review results before operational use, especially negative classifications and mixed signals. The fixture does not validate these linguistic failure modes.

## Two-week improvement hook and verdict

Start the window on the first real use, not the build date. Keep trial data outside git. For 14 days record runs actually used and hand-check a representative sample including classified and unclassified replies. Measure core error rate as disagreements / hand-checked replies; record denominator and sample selection. No sample means unmeasured, never zero error. Record the top failure cause. If measured error rate exceeds 10 percent, fix the most frequent cause and recheck, or kill with the reason. If there are no actual uses, kill with the reason.

Final evidence-based verdict is pending the two-week window. Provisional build verdict: maintain as portfolio evidence only. After the window choose expand for daily use or revenue, integrate for substantial sibling overlap, commercialise for demonstrated buyer willingness to pay, maintain as portfolio evidence otherwise, or kill for no use or unmet acceptance criteria. Record the actual choice and evidence in `VERDICT.md`. No real usage or buyer demand has been measured in this build.
