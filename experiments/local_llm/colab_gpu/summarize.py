"""Summarize GPU results into CSV + Markdown report (offline, stdlib only).

Usage: python3 summarize.py [--results DIR] [--report REPORT.md]
       [--cpu-log PATH] [--out-csv summary.csv]
Reads results/{bench_3c/bench_3c.jsonl, stage_3e/stage_3e.jsonl,
full/full.jsonl, preflight.json}. --cpu-log optionally points at the
sibling CPU study_3c.jsonl for side-by-side 3C numbers (labeled by
origin; non-equivalent runs are never merged).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import statistics
import sys
from pathlib import Path


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def mean(values: list):
    return round(statistics.mean(values), 3) if values else None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="summarize GPU results")
    parser.add_argument("--results", default="results")
    parser.add_argument("--report", default="results/REPORT.md")
    parser.add_argument("--out-csv", default="results/summary.csv")
    parser.add_argument("--cpu-log", default=None)
    args = parser.parse_args(argv)
    base = Path(args.results)

    bench = read_jsonl(base / "bench_3c" / "bench_3c.jsonl")
    e3 = read_jsonl(base / "stage_3e" / "stage_3e.jsonl")
    full = read_jsonl(base / "full" / "full.jsonl")
    preflight = {}
    if (base / "preflight.json").exists():
        with (base / "preflight.json").open("r", encoding="utf-8") as fh:
            preflight = json.load(fh)

    def lat(rows, key="request_s"):
        return [r[key] for r in rows
                if r.get(key) is not None and r.get("ok")]

    rows = []
    b_ok = [r for r in bench if r.get("ok") and r.get("valid")]
    rows.append(("3c_cases", len(bench), None))
    rows.append(("3c_valid", len(b_ok), None))
    rows.append(("3c_mean_s", mean(lat(bench)), "single-run means"))
    e_ok = [r for r in e3 if r.get("ok") and r.get("valid")]
    rows.append(("3e_cases", len(e3), None))
    rows.append(("3e_valid", len(e_ok), None))
    rows.append(("3e_mean_s", mean(lat(e3)), "single-run means"))
    f_ok = [r for r in full if r.get("ok")]
    rows.append(("full_cases", len(full), None))
    rows.append(("full_completed", len(f_ok), None))
    totals = [sum(v for v in (r.get("3c_s"), r.get("3e_s"), r.get("3f_s"))
                  if isinstance(v, (int, float))) for r in f_ok]
    rows.append(("full_total_mean_s", mean(totals), "sum of stage means"))

    cpu_note = "CPU reference not supplied."
    if args.cpu_log and Path(args.cpu_log).exists():
        cpu = read_jsonl(Path(args.cpu_log))
        cpu_ok = [r for r in cpu if r.get("ok") and r.get("valid")]
        cpu_note = ("CPU 3C study (%s): %d/%d valid, mean %.3f s "
                    "(separate machine/run; side-by-side only, not pooled)."
                    % (args.cpu_log, len(cpu_ok), len(cpu),
                       mean(lat(cpu)) or 0.0))

    with open(args.out_csv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value", "note"])
        writer.writerows(rows)

    buf = io.StringIO()
    buf.write("# GPU experiment report (machine-generated)\n\n")
    buf.write("Preflight GPU lines: %s\n\n" % json.dumps(
        preflight.get("nvidia_smi", "missing"))[:300])
    buf.write("| metric | value | note |\n|---|---|---|\n")
    for metric, value, note in rows:
        buf.write("| %s | %s | %s |\n" % (metric, value, note or ""))
    buf.write("\n%s\n" % cpu_note)
    buf.write("\nNo statistical significance is claimed. Sample sizes above.\n")
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    print(buf.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())
