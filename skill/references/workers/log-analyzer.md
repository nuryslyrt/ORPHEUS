# log-analyzer

A worker that analyzes ORPHEUS execution logs to find patterns, correlate errors, and extract insights.

## Purpose

Execution logs contain the full trace of what happened during a pipeline run — every decision, action, error, and result. This worker reads those logs and produces structured analysis. The Doctor uses it to diagnose failures and recurring issues. The Auditor uses it for log health checks. Without this worker, diagnosis would require manual reading of hundreds of log entry files.

## Contract

**Input:**
- `operation`: "analyze_execution" | "find_patterns" | "health_check"
- `log_paths`: Array of paths to log directories or assembled log files to analyze
- `focus`: (optional) Specific skill name, error type, or event category to zoom in on
- `execution_ids`: (optional) List of execution IDs to analyze (for cross-execution pattern finding)

**Output:**
- `findings`: Array of {type, severity, description, evidence, affected_skill, log_entry_ids[]}
- `patterns`: Array of {pattern_name, occurrences, description, example_entries[]}
- `health_status`: (health_check only) {log_structure_valid, missing_files[], corrupted_files[], coverage_score}

## Task Protocol

### For "analyze_execution":

Analyze a single execution to understand what happened and identify issues.

1. **Read the assembled logs** if they exist:
   - `errors.log.yaml` first — this is the fastest path to issues
   - `decisions.log.yaml` second — trace the reasoning that led to errors
   - `timeline.log.yaml` if deeper context is needed

2. **If assembled logs don't exist**, read raw entry files:
   - Scan `.orpheus/logs/runtime/{eid}/orchestrator/entry-*.yaml`
   - Scan `.orpheus/logs/runtime/{eid}/jobs/*/entry-*.yaml`
   - Sort by timestamp mentally to reconstruct the timeline

3. **For each error or warning found**, trace backwards:
   - What decision preceded this error? (find the nearest decision entry before the error timestamp from the same skill)
   - What was the input to the skill that failed? (read the job definition)
   - Was recovery attempted? Did it succeed?
   - Construct a finding with: what happened, why (based on decision reasoning), what skill, evidence (log entry IDs)

4. **If `focus` is specified**, filter analysis to only entries matching that skill, error type, or category.

5. **Write findings** to result_path.

### For "find_patterns":

Analyze across multiple executions to find recurring issues.

1. **Read assembled logs** from each execution ID in `execution_ids`

2. **Look for recurring patterns:**
   - Same error message appearing in multiple executions
   - Same skill failing repeatedly (even if error messages differ)
   - Same decision being made with low confidence across executions
   - Retry counts consistently hitting max_retries for specific jobs
   - Specific workers consistently producing empty or partial results
   - Increasing execution duration over time (performance degradation)

3. **For each pattern found**, collect:
   - Pattern name (descriptive, e.g., "recurring-web-search-timeout")
   - Number of occurrences across executions
   - Description of the pattern
   - Example log entries (2-3 representative entries)

4. **Write patterns** to result_path.

### For "health_check":

Verify log directory structure and file integrity.

1. **Check directory structure:**
   - Does `.orpheus/logs/runtime/{eid}/` exist for each execution?
   - Does each execution have `orchestrator/` and `jobs/` subdirectories?
   - Are there assembled views (timeline, decisions, errors, execution .log.yaml)?

2. **Check file integrity:**
   - Can each entry-*.yaml file be read without errors?
   - Does each entry have the required fields (id, timestamp, level, category, event, summary)?
   - Are timestamps in valid ISO 8601 format?

3. **Compute coverage score** (0.0 to 1.0):
   - 1.0 = all executions have complete log sets with assembled views
   - Deduct for: missing assembled views (-0.1 each), missing job log directories (-0.1 each), corrupted entry files (-0.1 each)

4. **Write health_status** to result_path.

## Output Format

```yaml
job_id: "{job_id}"
status: completed
skill_name: log-analyzer
output:
  findings:
    - type: "error_correlation"
      severity: high
      description: "web-search-worker consistently returns empty results when query contains version numbers"
      evidence:
        log_entry_ids: ["log-e001-012", "log-e001-015"]
        pattern: "3 of 4 web-search dispatches with version-specific queries returned 0 results"
      affected_skill: "web-search-worker"
  patterns:
    - pattern_name: "web-search-version-query-failure"
      occurrences: 3
      description: "Queries containing exact version strings (e.g., 'Apache 2.4.41') consistently fail"
      example_entries: ["log-e001-012", "log-e002-008"]
  health_status: null
```

## Constraints

- This worker is **READ-ONLY** — it never modifies log files or any other state
- Report ALL findings, not just the first — the Doctor needs the complete picture
- Always include evidence (specific log entry IDs) for every finding — unsubstantiated findings are useless
- When analyzing cross-execution patterns, look at the most recent 10 executions maximum to keep analysis focused
- If a log file is corrupted or unreadable, report it as a finding (type: "corrupted_log") and continue analyzing the rest
