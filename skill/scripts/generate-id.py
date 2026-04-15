#!/usr/bin/env python3
"""ORPHEUS ID Generator — Counter-based ID generation with prefix.

Usage: python3 generate-id.py <prefix> [--base-path <path>]

Prefixes:
  e = execution    (e001, e002, ...)
  b = build        (b001, b002, ...)
  s = surgeon op   (s001, s002, ...)
  d = doctor op    (d001, d002, ...)
  a = audit        (a001, a002, ...)

Outputs JSON to stdout: {"id": "e001"}
"""

import json
import os
import sys

VALID_PREFIXES = {"e", "b", "s", "d", "a"}


def load_counters(path):
    """Load counters from YAML file. Returns dict."""
    if not os.path.exists(path):
        return {p: 0 for p in VALID_PREFIXES}
    counters = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in VALID_PREFIXES:
                    try:
                        counters[key] = int(val)
                    except ValueError:
                        counters[key] = 0
    for p in VALID_PREFIXES:
        if p not in counters:
            counters[p] = 0
    return counters


def save_counters(path, counters):
    """Save counters to YAML file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for p in sorted(VALID_PREFIXES):
            f.write(f"{p}: {counters.get(p, 0)}\n")


def generate_id(prefix, base_path=".orpheus"):
    """Generate next ID for the given prefix."""
    counter_path = os.path.join(base_path, "state", ".counters.yaml")
    counters = load_counters(counter_path)
    counters[prefix] = counters.get(prefix, 0) + 1
    new_id = f"{prefix}{counters[prefix]:03d}"
    save_counters(counter_path, counters)
    return new_id


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: generate-id.py <prefix> [--base-path <path>]"}))
        sys.exit(1)

    prefix = sys.argv[1].lower()
    if prefix not in VALID_PREFIXES:
        print(json.dumps({"error": f"Invalid prefix '{prefix}'. Valid: {sorted(VALID_PREFIXES)}"}))
        sys.exit(1)

    base_path = ".orpheus"
    if "--base-path" in sys.argv:
        idx = sys.argv.index("--base-path")
        if idx + 1 < len(sys.argv):
            base_path = sys.argv[idx + 1]

    new_id = generate_id(prefix, base_path)
    print(json.dumps({"id": new_id}))


if __name__ == "__main__":
    main()
