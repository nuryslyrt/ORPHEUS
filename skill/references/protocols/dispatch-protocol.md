# ORPHEUS Dispatch Protocol

This document defines the exact format for composing Agent tool prompts when dispatching skills as subagents. Every dispatch in ORPHEUS — orchestrator to expert, expert to worker — follows these templates. It also defines the error chain format and worker instance ID conventions.

## Why This Matters

Subagents start with a fresh context. They know nothing about the ORPHEUS system, the current execution, or their role unless you tell them explicitly in the dispatch prompt. A badly composed prompt produces a subagent that improvises instead of following protocol.

## Orchestrator → Expert Dispatch

Use this template when the orchestrator dispatches a job to an expert:

```
You are operating within an ORPHEUS skill system called "{system_name}".

Your role: {expert_name}

--- BEGIN SKILL DEFINITION ---
{FULL CONTENTS OF THE EXPERT'S SKILL.MD — paste the entire file}
--- END SKILL DEFINITION ---

Your execution context:
  execution_id: {eid}
  job_path: .orpheus/state/execution/{eid}/jobs/{job_id}.yaml
  result_path: .orpheus/state/execution/{eid}/results/{job_id}.yaml
  context_path: .orpheus/state/execution/{eid}/context/{expert_name}.yaml
  log_path: .orpheus/logs/runtime/{eid}/jobs/{job_id}/
  scripts_path: .orpheus/scripts/
  available_workers:
    - {worker_name}: .orpheus/workers/{worker_name}/SKILL.md
    - {worker_name}: .orpheus/workers/{worker_name}/SKILL.md

Instructions:
1. Read your job definition from job_path
2. Execute according to your skill protocol above
3. Write your final results as YAML to result_path
4. Write log entries as individual YAML files to log_path (entry-001.yaml, entry-002.yaml, etc.)
5. Every decision you make MUST be logged with: question, options_considered, chosen, reasoning, confidence
6. If you encounter errors, use the Error Chain Format defined below to preserve the full error trail
```

### For Dependent Jobs

When a job depends on results from prior jobs, append this to the dispatch context:

```
  dependency_results:
    - job_id: {dep_job_id}
      result_path: .orpheus/state/execution/{eid}/results/{dep_job_id}.yaml

  IMPORTANT: Read the dependency results from their result_paths BEFORE starting
  your work. These contain outputs from prior pipeline stages that your job needs.
```

### User Context Block

When the orchestrator has extracted user constraints or preferences from the conversation, append this to the dispatch context:

```
  user_context:
    original_request: "{the user's exact words}"
    constraints:
      - "{constraint 1 — e.g., 'skip the exploit phase'}"
      - "{constraint 2 — e.g., 'use conservative settings'}"
    conversation_notes: "{any relevant context from earlier in the conversation}"
```

WHY: Subagents have no access to the conversation history. Without this block, the expert only sees the job definition and misses critical user intent that was expressed earlier. This causes the "lost context" problem where an expert ignores user preferences it never received.

## Expert → Worker Dispatch

Use this template when an expert dispatches a task to a worker:

```
You are a worker skill in an ORPHEUS system called "{system_name}".

Your role: {worker_name}
Instance ID: {worker_instance_id}

--- BEGIN SKILL DEFINITION ---
{FULL CONTENTS OF THE WORKER'S SKILL.MD — paste the entire file}
--- END SKILL DEFINITION ---

Your task context:
  execution_id: {eid}
  job_id: {job_id}
  worker_instance_id: {worker_instance_id}
  task:
    {structured task description — what the expert needs done}
  result_path: .orpheus/state/execution/{eid}/results/{job_id}-{worker_instance_id}.yaml
  log_path: .orpheus/logs/runtime/{eid}/jobs/{job_id}/

Instructions:
1. Execute your task protocol on the task described above
2. Write your results as YAML to result_path
3. Write log entries to log_path as entry-{worker_instance_id}-001.yaml, entry-{worker_instance_id}-002.yaml, etc.
4. If you encounter errors, use the Error Chain Format defined below
```

## Worker Instance IDs

When an expert dispatches workers, each dispatch MUST have a unique `worker_instance_id`. This prevents file collisions when the same worker type is dispatched multiple times in parallel.

### Naming Convention

```
{worker_name}-{brief_task_descriptor}
```

Examples:
- `web-search-worker-quantum-breakthroughs` (first search query)
- `web-search-worker-quantum-industry` (second search query, same worker type)
- `data-extract-worker-pdf-analysis` (extraction from PDF)
- `data-extract-worker-csv-parsing` (extraction from CSV, same worker type)

The task descriptor should be a 1-3 word kebab-case slug derived from the task being performed. This makes log files and result files human-readable:

```
Results:
  research-quantum-web-search-worker-quantum-breakthroughs.yaml
  research-quantum-web-search-worker-quantum-industry.yaml

Log entries:
  entry-web-search-worker-quantum-breakthroughs-001.yaml
  entry-web-search-worker-quantum-industry-001.yaml
```

### When Only One Instance

If a worker type is dispatched only once for a job, you MAY use just the worker name as the instance ID: `web-search-worker`. The instance ID pattern is only critical when the same worker type is dispatched multiple times.

## Error Chain Format

When errors occur, every level in the hierarchy MUST preserve the original error and wrap it with its own context. This creates a traceable chain that the user (and the Doctor) can follow from symptom to root cause.

### Error Chain YAML Structure

```yaml
error:
  level: "{orchestrator|expert|worker}"
  skill_name: "{skill that caught/produced the error}"
  message: "{what happened at THIS level — 1-2 sentences}"
  recovery_attempted: "{what this level tried to do about it, or null}"
  recovery_succeeded: false
  original_error: null   # null if this is the origin (deepest level)
```

### How Each Level Wraps Errors

**Worker (origin — deepest level):**
```yaml
error:
  level: worker
  skill_name: web-search-worker-quantum-breakthroughs
  message: "WebSearch returned 0 results for query 'CVE Apache 2.4.41'"
  recovery_attempted: "Retried with broader query 'Apache 2.4 vulnerabilities'"
  recovery_succeeded: false
  original_error: null
```

**Expert (wraps the worker error):**
```yaml
error:
  level: expert
  skill_name: vuln-analysis-expert
  message: "CVE lookup failed — worker returned empty results for 2 of 3 queries"
  recovery_attempted: "Dispatched alternative worker with modified query strategy"
  recovery_succeeded: false
  original_error:
    level: worker
    skill_name: web-search-worker-quantum-breakthroughs
    message: "WebSearch returned 0 results for query 'CVE Apache 2.4.41'"
    recovery_attempted: "Retried with broader query 'Apache 2.4 vulnerabilities'"
    recovery_succeeded: false
    original_error: null
```

**Orchestrator (wraps the expert error):**
```yaml
error:
  level: orchestrator
  skill_name: pentest-orchestrator
  message: "Job 'vuln-analysis' failed after 2 retries"
  recovery_attempted: "Retried job with same expert (attempt 2 of 2)"
  recovery_succeeded: false
  original_error:
    level: expert
    skill_name: vuln-analysis-expert
    message: "CVE lookup failed — worker returned empty results for 2 of 3 queries"
    recovery_attempted: "Dispatched alternative worker with modified query strategy"
    recovery_succeeded: false
    original_error:
      level: worker
      skill_name: web-search-worker-quantum-breakthroughs
      message: "WebSearch returned 0 results for query 'CVE Apache 2.4.41'"
      recovery_attempted: "Retried with broader query"
      recovery_succeeded: false
      original_error: null
```

### Rules for Error Chains

1. **NEVER flatten errors.** "Job failed" is useless. The chain must trace to the root cause.
2. **ALWAYS include recovery_attempted.** Even if it's "No recovery possible — reporting failure." This tells the Doctor what was already tried.
3. **Include error chains in the result file** when status=failed:
   ```yaml
   job_id: "vuln-analysis"
   status: failed
   skill_name: vuln-analysis-expert
   error: {the full error chain}
   ```
4. **Log the error chain** as well (in a log entry with level=error). The result file is the source of truth; the log entry makes it discoverable during timeline assembly.
5. **When recovery succeeds**, still log the error but mark `recovery_succeeded: true`. This helps the Doctor identify recurring issues even when they're recovered.

## Dispatch Guidelines

### Keep Prompts Focused
- Include the FULL SKILL.md content — the subagent needs the complete protocol
- Include PATHS to data, not the data itself (the subagent reads files on demand)
- Exception: for very small inputs (< 10 lines), inline them in the task description

### Worker SKILL.md Loading
- The expert reads a worker's SKILL.md content ONLY when it decides to dispatch that worker
- Do NOT include all worker SKILL.md contents in the expert's dispatch prompt
- The available_workers list gives paths — the expert reads whichever ones it needs

### Parallel Dispatch
- To dispatch multiple jobs/workers in parallel: include multiple Agent tool calls in a SINGLE message
- Each Agent call is independent — one prompt per subagent
- All Agent calls in the same message execute concurrently

### Log Entry File Naming
- Orchestrator entries: `entry-001.yaml`, `entry-002.yaml` in the orchestrator/ log dir
- Expert entries: `entry-001.yaml`, `entry-002.yaml` in the job's log dir
- Worker entries: `entry-{worker_instance_id}-001.yaml` in the SAME job's log dir as the expert
- This naming prevents conflicts when expert and workers write to the same directory
- When the same worker type is dispatched multiple times, the unique instance ID guarantees no collisions
