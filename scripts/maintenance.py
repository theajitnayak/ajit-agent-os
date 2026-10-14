"""Write evidence of one actual offline maintenance run. Never invent missing days."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run_record(output, run_date):
    today = datetime.datetime.now(datetime.timezone.utc).astimezone(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date()
    if run_date != today:
        raise ValueError("Record the actual India run date. Do not backfill or future-date runs.")
    commands = [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]]
    for suite in (None, "bench/extended-cases.json"):
        for stub in ("strict", "greedy", "fabricating"):
            command = [sys.executable, "bench/run.py", "--stub", stub, "--format", "json"]
            if suite:
                command += ["--cases", suite]
            commands.append(command)
    day = Path(output) / run_date.isoformat()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S-%f")
    target = day / timestamp
    target.mkdir(parents=True, exist_ok=True)
    results = []
    for i, command in enumerate(commands):
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        text = process.stdout + process.stderr
        name = f"run-{i}.txt"
        (target / name).write_text(text, encoding="utf-8")
        row = {"command": command[1:], "exit_code": process.returncode,
               "log": name, "log_sha256": hashlib.sha256(text.encode()).hexdigest()}
        if i and process.returncode == 0:
            row["metrics"] = json.loads(process.stdout)["metrics"]
        results.append(row)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    changes = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    record = {"schema_version": 1, "record_date": run_date.isoformat(),
              "executed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source_commit": commit, "local_changes": changes,
              "network_calls": 0, "live_model_evaluation": False,
              "fixture_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                  for name in ("bench/cases.json", "bench/extended-cases.json")},
              "runs": results, "limitations": ["Offline stubs only", "Developer-authored fictional cases",
                                                "Passing tests does not establish external adoption"]}
    (target / "record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (day / "latest.json").write_text(json.dumps({"record": f"{timestamp}/record.json"}), encoding="utf-8")
    passed = all(row["exit_code"] == 0 for row in results)
    (target / "record.md").write_text(
        f"# Maintenance record: {run_date}\n\nActual run: {record['executed_at_utc']}\n\n"
        f"Source commit: {commit}\n\nAll commands passed: {passed}\n\n"
        "Original and extended benchmarks are recorded separately. No provider API was called.\n\n"
        "See record.json for commands, metrics and evidence hashes. This records testing, not user adoption.\n",
        encoding="utf-8")
    return passed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date", type=datetime.date.fromisoformat, required=True)
    args = parser.parse_args()
    return 0 if run_record(args.output, args.date) else 1

if __name__ == "__main__":
    sys.exit(main())
