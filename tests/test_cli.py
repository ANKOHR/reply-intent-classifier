import json
import time
import pytest
from reply_intent_classifier.cli import main


def test_run_completes_on_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    started = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - started < 5


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report"]) == 0
    assert "Total records: 0" in capsys.readouterr().out

@pytest.mark.parametrize("name,content,line", [("bad.json", '{\ninvalid}', 2), ("bad.jsonl", '# comment\ninvalid', 2), ("bad.csv", 'id,text,synthetic\na,"unterminated,true', 2), ("bad.yaml", 'x: [', 1)])
def test_malformed_input_named_error(tmp_path, capsys, name, content, line):
    (tmp_path / name).write_text(content)
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert name in error and f"line {line}" in error and "Error" in error
    assert "Traceback" not in error


def test_determinism_byte_identical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    first = (tmp_path / ".ric/results.json").read_bytes()
    main(["run", "--input", "demo"])
    assert first == (tmp_path / ".ric/results.json").read_bytes()
    for format in ("md", "json"):
        main(["report", "--format", format, "--out", "a.txt"])
        main(["report", "--format", format, "--out", "b.txt"])
        assert (tmp_path / "a.txt").read_bytes() == (tmp_path / "b.txt").read_bytes()


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for command in ("fixtures", "run", "report", "classify", "audit"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "json"]) == 0
    assert main(["classify", "--text", "No thanks"]) == 0
    assert main(["audit", "--input", "demo"]) == 0


def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_write_failure_no_partial_files(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    (tmp_path / "blocked").mkdir()
    before = set(tmp_path.iterdir())
    assert main(["report", "--out", "blocked"]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert before == set(tmp_path.iterdir())


def test_csv_and_real_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/replies.csv").write_text('id,text,synthetic,source,expected\na,No thanks,false,henry_entered,negative\n')
    assert main(["run", "--input", "data"]) == 0
    result = json.loads((tmp_path / ".ric/results.json").read_text())
    assert result["evaluation"]["correct"] == 1


def test_tampered_aggregates_recomputed(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    path = tmp_path / ".ric/results.json"
    result = json.loads(path.read_text())
    result["total"] = 999
    path.write_text(json.dumps(result))
    capsys.readouterr()
    assert main(["report"]) == 0
    assert "Total records: 200" in capsys.readouterr().out

@pytest.mark.parametrize("record,field", [({"id":"a","text":"x","synthetic":True,"amount":-1}, "amount"), ({"id":"a","text":"x","synthetic":True,"received_at":"2099-01-01"}, "received_at")])
def test_file_schema_errors_name_field_and_line(tmp_path, capsys, record, field):
    (tmp_path / "replies.jsonl").write_text(json.dumps(record))
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert field in error and "replies.jsonl" in error and "line 1" in error


def test_empty_csv_text_is_unclassified(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/replies.csv").write_text("id,text,synthetic\na,,true\n")
    assert main(["run", "--input", "data"]) == 0
    assert json.loads((tmp_path / ".ric/results.json").read_text())["counts"]["unclassified"] == 1
