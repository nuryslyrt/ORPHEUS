# registry-updater

A worker that creates or updates the registry.yaml file for ORPHEUS skill systems.

## Purpose

The registry is the index of all skills in a system. This worker maintains it — creating the initial registry when a system is built, adding/removing entries when skills are modified, and scanning for integrity issues during audits.

## Contract

**Input:**
- `operation`: "create" | "add_entry" | "remove_entry" | "update_entry" | "scan"
- `registry_path`: Path to the registry.yaml file
- `system_name`: Name of the system (for "create")
- `entry`: Object with skill details (for add/update):
  - `section`: "orchestrator" | "experts" | "workers"
  - `name`, `path`, `version`, `contract`, `tags`, `compatible_workers` (experts), `model_preference` (workers)
- `target`: Skill name to remove (for "remove_entry")
- `system_path`: Path to .orpheus/ root (for "scan")

**Output:**
- `file_path`: Path to the registry.yaml
- `changes_made`: List of changes applied
- `integrity_report`: (scan only) {total_skills, missing_files[], orphaned_files[], valid: bool}

## Task Protocol

### For "create":

1. Read `templates/registry.yaml.tmpl`
2. Fill `{{SYSTEM_NAME}}` with the provided system_name
3. Fill `{{VERSION}}` with "1.0.0"
4. Fill `{{ORCHESTRATOR_ENTRY}}`, `{{EXPERT_ENTRIES}}`, `{{WORKER_ENTRIES}}` with the provided entries
5. Write to `registry_path`

### For "add_entry":

1. Read the current registry.yaml from `registry_path`
2. Add the new entry to the appropriate section (experts or workers array)
3. Ensure no duplicate names exist
4. Write the updated registry.yaml

### For "remove_entry":

1. Read the current registry.yaml
2. Find the entry with matching name in the specified section
3. Remove it
4. Also remove it from any `compatible_workers` lists in expert entries
5. Write the updated registry.yaml

### For "update_entry":

1. Read the current registry.yaml
2. Find the entry with matching name
3. Update the specified fields (preserve fields not mentioned)
4. Write the updated registry.yaml

### For "scan" (read-only integrity check):

1. Read the registry.yaml
2. For each skill entry, check that the `path` file exists on disk
3. For each skill entry, check that the `contract` file exists on disk
4. Scan the .orpheus/ directory for skill files NOT in the registry (orphaned)
5. Report: total skills, missing files, orphaned files, overall validity

## Output Format

```yaml
job_id: "{job_id}"
status: completed
skill_name: registry-updater
output:
  file_path: "{registry_path}"
  changes_made:
    - "Added expert: research-expert"
  integrity_report: null
```

For scan operations:
```yaml
output:
  file_path: "{registry_path}"
  changes_made: []
  integrity_report:
    total_skills: 8
    missing_files: []
    orphaned_files: []
    valid: true
```

## Constraints

- NEVER create duplicate entries — check for existing names before adding
- NEVER modify the registry during a "scan" operation — scans are strictly read-only
- All paths in registry entries must be relative to the .orpheus/ root
- Skill names must be unique across ALL sections (an expert and worker cannot share a name)
