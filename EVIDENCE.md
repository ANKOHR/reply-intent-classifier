# Local build evidence

Measured on 2026-10-01 with Python 3.12.10 on Windows, CPU only.

- Pytest: 44 passed.
- Installed `ric` executable: fixtures, run and Markdown report completed in 0.825 seconds total using three fresh processes. Acceptance threshold: under 5 seconds.
- SYNTHETIC fixture: 200 records; 40 in each of five intents; zero unclassified; 200 supplied labels correct; zero labelled false positives.
- Tests verify byte-identical repeated saved results and Markdown/JSON reports, corrupted labels changing figures, empty input, malformed input, duplicate ids, future dates, negative amounts as unsupported fields, Unicode and long strings, and atomic report write failure.
- No real trial, time-savings baseline or financial benefit measured. Final verdict awaits the two-week real-use window.

Measured demo output follows. All data below is SYNTHETIC.

```text
SYNTHETIC: generated 200 planted records and hand-computed expectations.
Computed 200 records. Phrase matches computed from supplied text. Accuracy measured only against supplied labels; not independent validation. Time and money savings unmeasured and not reported.
Data provenance: SYNTHETIC fixtures=200; real Henry-entered records=0 (input declaration, not independently verified).
# Reply Intent Classifier

Data provenance: SYNTHETIC fixtures=200; real Henry-entered records=0 (input declaration, not independently verified).

Phrase matches computed from supplied text. Accuracy measured only against supplied labels; not independent validation. Time and money savings unmeasured and not reported.

Total records: 200
Manual review required: 10

| Intent | Count | Labelled false positives |
| --- | ---: | ---: |
| positive | 40 | 0 |
| negative | 40 | 0 |
| objection | 40 | 0 |
| timing | 40 | 0 |
| referral | 40 | 0 |
| unclassified | 0 | 0 |

Supplied labels: 200; unlabelled: 0; correct: 200; errors: 0.
Accuracy against supplied labels: 1.000000

Per-record evidence and confusion matrix are available in the JSON report.
```
