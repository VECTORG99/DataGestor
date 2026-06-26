"""
Generate frontend-facing JSONs from live pipeline metrics.

Reads the latest entry from data/metrics/pipeline_metrics.jsonl (written by
MetricsCollector during pipeline execution) and updates:
  - apps/frontend/public/pipeline_logs.json  ← run metrics + cleaning details
  - apps/frontend/public/pipeline_stats.json  ← stage descriptions + record counts

Usage:
  python -m apps.backend.cli.generate_frontend_jsons
  python -m apps.backend.cli.generate_frontend_jsons --run-id 2026-06-21T07:18:33

Designed to be called at the end of pipeline_dataops.py or standalone.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
METRICS_FILE = PROJECT_ROOT / "data" / "metrics" / "pipeline_metrics.jsonl"
FRONTEND_PUBLIC = PROJECT_ROOT / "apps" / "frontend" / "public"
LOGS_FILE = FRONTEND_PUBLIC / "pipeline_logs.json"
STATS_FILE = FRONTEND_PUBLIC / "pipeline_stats.json"


def read_latest_metrics() -> dict | None:
    """Read the last (most recent) entry from pipeline_metrics.jsonl."""
    if not METRICS_FILE.exists():
        print(f"  [WARN] Metrics file not found: {METRICS_FILE}", file=sys.stderr)
        return None
    with open(METRICS_FILE) as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    if not lines:
        print(f"  [WARN] Metrics file is empty: {METRICS_FILE}", file=sys.stderr)
        return None
    last = json.loads(lines[-1])
    print(
        f"  [OK]   Latest run: {last.get('timestamp', '?')}  "
        f"duration={last.get('total_duration_seconds', '?')}s  "
        f"records={last.get('records_initial', '?')} -> {last.get('records_final', '?')}"
    )
    return last


def to_production_run(metrics: dict) -> dict:
    """Convert a PipelineMetrics dict to a production_runs entry."""
    stages_out = []
    for s in metrics.get("stages", []):
        entry = {
            "stage": s["stage"],
            "duration_s": round(s.get("duration_seconds", 0), 2),
        }
        if s.get("records_in") is not None:
            entry["records_in"] = s["records_in"]
        if s.get("records_out") is not None:
            entry["records_out"] = s["records_out"]
        if (
            s.get("records_in") is not None
            and s.get("records_out") is not None
            and s["records_in"] > 0
        ):
            reduction = (1 - s["records_out"] / s["records_in"]) * 100
            entry["reduction_pct"] = round(reduction, 1)
        stages_out.append(entry)

    return {
        "run_id": metrics.get("timestamp", "unknown").split("T")[0],
        "mode": "Demo" if metrics.get("demo_mode") else "Produccion",
        "duration_seconds": round(metrics.get("total_duration_seconds", 0), 1),
        "stages": stages_out,
        "total_records_in": metrics.get("records_initial", 0),
        "total_records_out": metrics.get("records_final", 0),
        "completeness_pct": round(metrics.get("completeness_pct", 100.0), 1),
        "warnings_count": metrics.get("warnings_count", 0),
        "peak_memory_mb": round(metrics.get("peak_memory_mb", 0), 1),
        "avg_cpu_percent": round(metrics.get("avg_cpu_percent", 0), 1),
    }


def update_logs(logs: dict, run: dict) -> dict:
    """Replace the first production run in logs with live data."""
    logs = json.loads(json.dumps(logs))  # deep copy
    # Prepend new run, keep existing runs as history
    logs["production_runs"].insert(0, run)
    # Keep only the 5 most recent runs
    logs["production_runs"] = logs["production_runs"][:5]
    return logs


def update_stats(stats: dict, run: dict) -> dict:
    """Update record counts in pipeline_stats.json from the run data."""
    stats = json.loads(json.dumps(stats))
    for s in stats.get("stages", []):
        if s["stage"] == "crudos":
            if run.get("total_records_in"):
                s["records"] = f"~{run['total_records_in']:,}"
        elif s["stage"] == "agregacion":
            if run.get("total_records_out"):
                s["records_out"] = f"{run['total_records_out']:,}"
        elif s["stage"] == "total_crimenes":
            # Can't derive the crime sum from metrics alone; skip
            pass
    return stats


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Generate frontend JSONs from pipeline metrics")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print what would change without writing"
    )
    args = parser.parse_args(argv)

    latest = read_latest_metrics()
    if latest is None:
        print("  [SKIP] No metrics data available. JSON files left unchanged.")
        return

    run = to_production_run(latest)
    print(
        f"  [OK]   Built production run entry: {run['run_id']}  {run['mode']}  {run['duration_seconds']}s"
    )

    # --- Update pipeline_logs.json ---
    if not LOGS_FILE.exists():
        print(f"  [WARN] {LOGS_FILE} not found. Creating skeleton.", file=sys.stderr)
        logs = {"production_runs": [], "cleaning_details": [], "recent_entries": []}
    else:
        with open(LOGS_FILE) as f:
            logs = json.load(f)

    logs = update_logs(logs, run)

    if args.dry_run:
        print(f"  [DRY]  Would write {LOGS_FILE}")
        print(f"         production_runs: {len(logs['production_runs'])} runs")
    else:
        with open(LOGS_FILE, "w") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        print(f"  [OK]   Updated {LOGS_FILE}")

    # --- Update pipeline_stats.json (record counts only) ---
    if STATS_FILE.exists():
        with open(STATS_FILE) as f:
            stats = json.load(f)
        stats = update_stats(stats, run)
        if args.dry_run:
            print(f"  [DRY]  Would write {STATS_FILE}")
        else:
            with open(STATS_FILE, "w") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"  [OK]   Updated {STATS_FILE}")
    else:
        print(f"  [SKIP] {STATS_FILE} not found — skipping stats update")


if __name__ == "__main__":
    # When invoked directly from CLI, let argparse read sys.argv normally.
    # --dry-run flag available for testing.
    main()
