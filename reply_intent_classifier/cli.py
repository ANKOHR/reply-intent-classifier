"""Local CLI. Data is never sent to external services."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import AS_OF, InputError, analyze, classify
from .fixtures import generate
from .report import render


def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(content)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from None
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def read_inputs(directory, as_of=AS_OF):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use ric fixtures --out demo or supply an input directory")
    records = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name in ("expectations.json", "tiny.example.json") or path.name.startswith("."):
            continue
        if path.suffix.lower() not in (".json", ".jsonl", ".csv"):
            raise InputError(f"SchemaError: {path}: line 1: unsupported format; use JSON, JSONL or CSV")
        try:
            content = path.read_text(encoding="utf-8-sig")
            entries = []
            if path.suffix.lower() == ".jsonl":
                for line, value in enumerate(content.splitlines(), 1):
                    if value.strip() and not value.lstrip().startswith("#"):
                        try:
                            entries.append((line, json.loads(value)))
                        except json.JSONDecodeError as exc:
                            raise InputError(f"ParseError: {path}: line {line}: {exc.msg}") from None
            elif path.suffix.lower() == ".json":
                payload = json.loads(content)
                values = payload.get("records") if isinstance(payload, dict) else payload
                if not isinstance(values, list):
                    raise InputError(f"SchemaError: {path}: line 1: expected list or records envelope")
                entries = [(1, value) for value in values]
            else:
                reader = csv.DictReader(io.StringIO(content), strict=True)
                fields = reader.fieldnames or []
                allowed = {"id", "text", "synthetic", "expected", "source", "received_at"}
                if len(fields) != len(set(fields)) or not {"id", "text", "synthetic"}.issubset(fields) or set(fields) - allowed:
                    raise InputError(f"SchemaError: {path}: line 1: invalid CSV fields {fields}")
                for value in reader:
                    if None in value or any(v is None for v in value.values()):
                        raise InputError(f"ParseError: {path}: line {reader.line_num}: wrong CSV field count")
                    if value.get("synthetic") not in ("true", "false"):
                        raise InputError(f"SchemaError: {path}: line {reader.line_num}: synthetic must be true or false")
                    value["synthetic"] = value["synthetic"] == "true"
                    entries.append((reader.line_num, {k: v for k, v in value.items() if v != "" or k in ("id", "text")}))
            from .core import validate
            for line, value in entries:
                try:
                    validate(value, as_of)
                    if any(r["id"] == value["id"] for r in records):
                        raise InputError("SchemaError: duplicate id " + value["id"])
                except InputError as exc:
                    raise InputError(f"{exc}: {path}: line {line}") from None
                records.append(value)
        except json.JSONDecodeError as exc:
            raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from None
        except csv.Error as exc:
            raise InputError(f"ParseError: {path}: line {reader.reader.line_num}: {exc}") from None
        except (OSError, UnicodeError) as exc:
            raise InputError(f"ReadError: {path}: line 1: {exc}") from None
    return records



def parser():
    p = argparse.ArgumentParser(prog="ric", description="Deterministic phrase classification of local replies. No predictive accuracy claim.")
    subs = p.add_subparsers(dest="command", required=True)
    f = subs.add_parser("fixtures", help="Generate 200 labelled synthetic examples", epilog="Example: ric fixtures --out demo")
    f.add_argument("--out", required=True)
    r = subs.add_parser("run", help="Classify input and save measured results", epilog="Example: ric run --input demo")
    r.add_argument("--input", required=True)
    r.add_argument("--state", default=".ric/results.json")
    r.add_argument("--as-of", default=AS_OF, help="ISO date cutoff, default fixed 2026-09-30")
    report = subs.add_parser("report", help="Render provenance-bearing results", epilog="Example: ric report --format md")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--state", default=".ric/results.json")
    report.add_argument("--out")
    c = subs.add_parser("classify", help="Explain phrase matches for one synthetic example", epilog='Example: ric classify --text "No thanks"')
    c.add_argument("--text", required=True)
    a = subs.add_parser("audit", help="Compare classifications with supplied hand-checked labels", epilog="Example: ric audit --input demo")
    a.add_argument("--input", required=True)
    a.add_argument("--as-of", default=AS_OF)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("SYNTHETIC: generated 200 planted records and hand-computed expectations.")
        elif args.command in ("run", "audit"):
            from datetime import date
            try:
                date.fromisoformat(args.as_of)
            except ValueError:
                raise InputError("SchemaError: as_of must be an ISO date") from None
            result = analyze(read_inputs(args.input, args.as_of), args.as_of)
            if args.command == "run":
                atomic_write(args.state, render(result, "json"))
                print(f"Computed {result['total']} records. " + result["honesty"])
                print(render(result).splitlines()[2])
            else:
                print(render(result, "json"), end="")
        elif args.command == "classify":
            from .core import validate
            validate({"id": "example", "text": args.text, "synthetic": True})
            print(json.dumps({"provenance": "SYNTHETIC illustrative text argument; no measured accuracy", **classify(args.text)}, ensure_ascii=True, sort_keys=True))
        else:
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f"MissingInput: {path}; run ric run --input <dir> first")
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
                if result.get("schema_version") != 1:
                    raise ValueError("unsupported schema_version")
                # Recompute from saved explicit records, rejecting stale or tampered aggregates.
                originals = [{k: v for k, v in row.items() if k not in ("label", "matches", "review_required")} for row in result["records"]]
                result = analyze(originals, result["as_of"])
                content = render(result, args.format)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"SchemaError: {path}: line 1: invalid saved results: {exc}") from None
            if args.out:
                atomic_write(args.out, content)
            else:
                print(content, end="")
        return 0
    except (InputError, OSError) as exc:
        print(str(exc).replace(chr(0x2014), "-"), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
