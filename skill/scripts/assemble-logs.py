#!/usr/bin/env python3
"""ORPHEUS Log Assembler — Merges per-entry log files into assembled views.

Usage: python3 assemble-logs.py <execution-id> [--base-path <path>]

Reads per-entry YAML files from:
  - .orpheus/logs/runtime/{eid}/jobs/{job-id}/entry-*.yaml
  - .orpheus/logs/runtime/{eid}/orchestrator/entry-*.yaml

Produces:
  - .orpheus/logs/runtime/{eid}/timeline.log.yaml    (all entries, sorted by timestamp)
  - .orpheus/logs/runtime/{eid}/decisions.log.yaml   (decision entries only)
  - .orpheus/logs/runtime/{eid}/errors.log.yaml      (warn/error/fatal entries only)
  - .orpheus/logs/runtime/{eid}/execution.log.yaml   (master summary)

Outputs JSON summary to stdout.
"""

import glob
import json
import os
import sys
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_entry(filepath):
    """Parse a single log entry YAML file."""
    if HAS_YAML:
        with open(filepath, "r") as f:
            return yaml.safe_load(f) or {}
    # Basic fallback parser
    data = {}
    with open(filepath, "r") as f:
        content = f.read()
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        if ":" in stripped and not stripped.startswith(" "):
            key, val = stripped.split(":", 1)
            data[key.strip()] = val.strip().strip("\"'")
    return data


def write_yaml(filepath, data):
    """Write data as YAML."""
    if HAS_YAML:
        with open(filepath, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:
        with open(filepath, "w") as f:
            f.write(json.dumps(data, indent=2, default=str))


def collect_entries(log_dir):
    """Collect all entry files from a log directory tree."""
    entries = []
    # Orchestrator entries
    orch_dir = os.path.join(log_dir, "orchestrator")
    if os.path.isdir(orch_dir):
        for fp in sorted(glob.glob(os.path.join(orch_dir, "entry-*.yaml"))):
            entry = parse_entry(fp)
            if entry:
                entry["_source_file"] = fp
                entries.append(entry)

    # Per-job entries
    jobs_dir = os.path.join(log_dir, "jobs")
    if os.path.isdir(jobs_dir):
        for job_dir in sorted(os.listdir(jobs_dir)):
            job_path = os.path.join(jobs_dir, job_dir)
            if os.path.isdir(job_path):
                for fp in sorted(glob.glob(os.path.join(job_path, "entry-*.yaml"))):
                    entry = parse_entry(fp)
                    if entry:
                        entry["_source_file"] = fp
                        entries.append(entry)

    return entries


def sort_by_timestamp(entries):
    """Sort entries by timestamp field."""
    def get_ts(e):
        ts = e.get("timestamp", "")
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.min
    return sorted(entries, key=get_ts)


def strip_internal(entry):
    """Remove internal fields before writing."""
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def assemble(execution_id, base_path=".orpheus"):
    """Assemble all log views for an execution."""
    log_dir = os.path.join(base_path, "logs", "runtime", execution_id)

    if not os.path.isdir(log_dir):
        return {"error": f"Log directory not found: {log_dir}"}

    # Collect and sort all entries
    all_entries = collect_entries(log_dir)
    sorted_entries = sort_by_timestamp(all_entries)
    clean_entries = [strip_internal(e) for e in sorted_entries]

    # Timeline: all entries
    timeline = {
        "execution_id": execution_id,
        "timeline": clean_entries,
    }
    write_yaml(os.path.join(log_dir, "timeline.log.yaml"), timeline)

    # Decisions: category == "decision" only
    decision_entries = [e for e in clean_entries if e.get("category") == "decision"]
    decisions = {
        "execution_id": execution_id,
        "total_decisions": len(decision_entries),
        "decisions": decision_entries,
    }
    write_yaml(os.path.join(log_dir, "decisions.log.yaml"), decisions)

    # Errors: level in (warn, error, fatal)
    error_levels = {"warn", "error", "fatal"}
    error_entries = [e for e in clean_entries if e.get("level") in error_levels]
    errors = {
        "execution_id": execution_id,
        "total_errors": len([e for e in error_entries if e.get("level") in ("error", "fatal")]),
        "total_warnings": len([e for e in error_entries if e.get("level") == "warn"]),
        "entries": error_entries,
    }
    write_yaml(os.path.join(log_dir, "errors.log.yaml"), errors)

    # Execution summary
    levels = {}
    categories = {}
    skills = set()
    for e in clean_entries:
        lvl = e.get("level", "unknown")
        levels[lvl] = levels.get(lvl, 0) + 1
        cat = e.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        src = e.get("source", {})
        if isinstance(src, dict) and "skill_name" in src:
            skills.add(src["skill_name"])

    execution_log = {
        "execution_id": execution_id,
        "status": "completed",
        "total_entries": len(clean_entries),
        "summary": {
            "total_decisions": len(decision_entries),
            "total_errors": errors["total_errors"],
            "total_warnings": errors["total_warnings"],
            "total_skills_invoked": len(skills),
            "levels": levels,
            "categories": categories,
        },
        "entries": [e for e in clean_entries if e.get("level") in ("info", "warn", "error", "fatal")],
    }
    write_yaml(os.path.join(log_dir, "execution.log.yaml"), execution_log)

    return {
        "status": "assembled",
        "execution_id": execution_id,
        "total_entries": len(clean_entries),
        "total_decisions": len(decision_entries),
        "total_errors": errors["total_errors"],
        "total_warnings": errors["total_warnings"],
        "files_written": [
            "timeline.log.yaml",
            "decisions.log.yaml",
            "errors.log.yaml",
            "execution.log.yaml",
        ],
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: assemble-logs.py <execution-id> [--base-path <path>]"}))
        sys.exit(1)

    execution_id = sys.argv[1]
    base_path = ".orpheus"

    if "--base-path" in sys.argv:
        idx = sys.argv.index("--base-path")
        if idx + 1 < len(sys.argv):
            base_path = sys.argv[idx + 1]

    result = assemble(execution_id, base_path)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
