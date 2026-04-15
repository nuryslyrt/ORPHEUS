#!/usr/bin/env python3
"""ORPHEUS YAML Validator — Validates YAML files against ORPHEUS schemas.

Usage: python3 validate-yaml.py <file-path> <schema-name>

Schema names: job, contract, log-entry, registry, system, manifest

Outputs JSON: {"valid": true/false, "errors": [...], "warnings": [...]}
"""

import json
import os
import sys

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# --- Schema Definitions ---
# Each schema defines required fields and their expected types/constraints.

SCHEMAS = {
    "job": {
        "required": {
            "job_id": "string",
            "title": "string",
            "status": {"enum": ["pending", "dispatched", "running", "completed", "failed"]},
            "assigned_expert": "string",
        },
        "optional": {
            "priority": "number",
            "dependencies": "list",
            "retry_count": "number",
            "input": "object",
            "expected_output": "object",
            "metadata": "object",
        },
    },
    "contract": {
        "required": {
            "name": "string",
            "version": "string",
        },
        "optional": {
            "input": "object",
            "output": "object",
        },
    },
    "log-entry": {
        "required": {
            "id": "string",
            "timestamp": "string",
            "execution_id": "string",
            "source": "object",
            "level": {"enum": ["trace", "debug", "info", "warn", "error", "fatal"]},
            "category": {"enum": [
                "action", "decision", "state_change", "delegation",
                "result", "error", "lifecycle", "contract", "system"
            ]},
            "event": "string",
            "summary": "string",
        },
        "optional": {
            "detail": "object",
            "decision": "object",
            "correlation": "object",
        },
    },
    "registry": {
        "required": {
            "system": "string",
            "version": "string",
            "skills": "object",
        },
        "optional": {},
    },
    "system": {
        "required": {
            "system": "object",
        },
        "optional": {
            "orchestrator": "object",
            "logging": "object",
        },
    },
    "manifest": {
        "required": {
            "execution_id": "string",
            "system": "string",
            "status": {"enum": ["pending", "running", "completed", "failed", "paused"]},
        },
        "optional": {
            "started_at": "string",
            "completed_at": "string",
            "user_request": "string",
            "plan": "object",
            "jobs": "object",
        },
    },
}


def parse_yaml_basic(filepath):
    """Basic YAML parser using line-by-line parsing when PyYAML unavailable."""
    data = {}
    with open(filepath, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue
            if ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val == "" or val.startswith("{") or val.startswith("["):
                    data[key] = {}  # Treat as object/list
                elif val.lower() in ("true", "false"):
                    data[key] = val.lower() == "true"
                elif val.isdigit():
                    data[key] = int(val)
                else:
                    data[key] = val.strip("\"'")
    return data


def parse_yaml(filepath):
    """Parse YAML file, with fallback."""
    if HAS_YAML:
        with open(filepath, "r") as f:
            return yaml.safe_load(f) or {}
    return parse_yaml_basic(filepath)


def check_type(value, expected_type):
    """Check if a value matches the expected type constraint."""
    if isinstance(expected_type, dict) and "enum" in expected_type:
        return value in expected_type["enum"]
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float))
    if expected_type == "list":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True


def validate(data, schema_name):
    """Validate data against a named schema."""
    errors = []
    warnings = []

    if schema_name not in SCHEMAS:
        return {"valid": False, "errors": [f"Unknown schema: {schema_name}"], "warnings": []}

    schema = SCHEMAS[schema_name]

    # Check required fields
    for field, expected_type in schema["required"].items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not check_type(data[field], expected_type):
            if isinstance(expected_type, dict) and "enum" in expected_type:
                errors.append(
                    f"Field '{field}' has invalid value '{data[field]}'. "
                    f"Valid values: {expected_type['enum']}"
                )
            else:
                errors.append(f"Field '{field}' has wrong type. Expected: {expected_type}")

    # Check for unknown fields (warning, not error)
    all_known = set(schema["required"]) | set(schema.get("optional", {}))
    for field in data:
        if field not in all_known:
            warnings.append(f"Unknown field: {field}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: validate-yaml.py <file-path> <schema-name>",
            "valid_schemas": list(SCHEMAS.keys()),
        }))
        sys.exit(1)

    filepath = sys.argv[1]
    schema_name = sys.argv[2]

    if not os.path.exists(filepath):
        print(json.dumps({"valid": False, "errors": [f"File not found: {filepath}"], "warnings": []}))
        sys.exit(1)

    try:
        data = parse_yaml(filepath)
    except Exception as e:
        print(json.dumps({"valid": False, "errors": [f"YAML parse error: {str(e)}"], "warnings": []}))
        sys.exit(1)

    result = validate(data, schema_name)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
