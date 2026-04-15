# ORPHEUS State Protocol

This document defines the filesystem state bus conventions. All inter-skill communication in ORPHEUS happens through files on disk. There are no in-memory channels, no message queues, no databases.

## Why Filesystem

The coding agent already has full file I/O. Files persist across subagent boundaries. Files are readable by any subagent. Files provide a natural audit trail. No additional infrastructure needed.

## Directory Layout

```
.orpheus/
├── state/
│   ├── .counters.yaml                    # ID generation counters
│   ├── execution/
│   │   └── {execution-id}/
│   │       ├── manifest.yaml             # Execution plan and status
│   │       ├── jobs/
│   │       │   └── {job-id}.yaml         # Job definitions
│   │       ├── results/
│   │       │   ├── {job-id}.yaml         # Expert's final result
│   │       │   └── {job-id}-{worker}.yaml # Worker's partial result
│   │       └── context/
│   │           └── {skill-name}.yaml     # Per-skill working state
│   └── shared/
│       └── {key}.yaml                    # Cross-execution shared data
├── logs/
│   ├── build/
│   │   └── {build-id}/                   # Builder/Surgeon/Doctor/Auditor logs
│   └── runtime/
│       └── {execution-id}/
│           ├── orchestrator/             # Orchestrator log entries
│           │   └── entry-{NNN}.yaml
│           ├── jobs/
│           │   └── {job-id}/             # Per-job log entries (expert + workers)
│           │       ├── entry-{NNN}.yaml
│           │       └── entry-{worker}-{NNN}.yaml
│           ├── timeline.log.yaml         # Assembled: all entries sorted by time
│           ├── decisions.log.yaml        # Assembled: decision entries only
│           ├── errors.log.yaml           # Assembled: warn/error/fatal only
│           └── execution.log.yaml        # Assembled: master summary
```

## Who Creates What

| Actor | Creates | When |
|-------|---------|------|
| **Orchestrator** | Execution directory tree (via `init-execution.sh`) | At execution start |
| **Orchestrator** | `manifest.yaml` | After planning, before dispatch |
| **Orchestrator** | `jobs/{job-id}.yaml` | During Phase 1 (decomposition) |
| **Orchestrator** | Assembled log views | During Phase 4 (via `assemble-logs.py`) |
| **Expert** | `results/{job-id}.yaml` | After completing its job |
| **Expert** | `context/{expert-name}.yaml` | During execution (intermediate state) |
| **Expert** | Job log directory entries | Throughout execution |
| **Worker** | `results/{job-id}-{worker-name}.yaml` | After completing its task |
| **Worker** | Job log entries (prefixed) | Throughout execution |

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Job definition | `{job-id}.yaml` | `research-quantum.yaml` |
| Expert result | `{job-id}.yaml` | `research-quantum.yaml` |
| Worker result | `{job-id}-{worker-name}.yaml` | `research-quantum-web-search-worker.yaml` |
| Context | `{skill-name}.yaml` | `research-expert.yaml` |
| Log entry (expert) | `entry-{NNN}.yaml` | `entry-001.yaml` |
| Log entry (worker) | `entry-{worker-name}-{NNN}.yaml` | `entry-web-search-worker-001.yaml` |

All names use **kebab-case** (lowercase, hyphens, no spaces).

## Scoped Access Rules

These are enforced by convention in skill instructions, not by filesystem permissions.

| Skill Type | Can Write To | Can Read From |
|------------|-------------|---------------|
| **Orchestrator** | manifest.yaml, jobs/*.yaml, assembled logs | Everything |
| **Expert** | Its own result, context, and log entries | Its job definition, dependency results, worker results |
| **Worker** | Its own result and log entries | Its task context (from dispatch prompt) |

**Why scoped access matters:** Without scoping, a worker could read another job's results and make decisions based on context it shouldn't have. This would produce unpredictable behavior and make debugging impossible.

## Execution Manifest

The orchestrator maintains a manifest tracking overall execution state:

```yaml
execution_id: "e001"
system: "content-pipeline"
status: running
started_at: "2026-04-12T14:00:00.000Z"
user_request: "Research AI trends and write a report"
plan:
  batches:
    - batch: 1
      jobs: [research-trends, analyze-competitors]
      status: completed
    - batch: 2
      jobs: [write-report]
      status: running
jobs:
  research-trends:
    status: completed
    result_path: results/research-trends.yaml
  analyze-competitors:
    status: completed
    result_path: results/analyze-competitors.yaml
  write-report:
    status: running
    dispatched_at: "2026-04-12T14:00:50.000Z"
```

## Result File Format

Expert and worker results follow a common structure:

```yaml
job_id: "{job-id}"
status: completed           # or failed
skill_name: "{skill-name}"
workers_invoked: []          # list of worker names used (experts only)
output:
  {arbitrary output fields matching the contract}
duration_seconds: 45
completed_at: "2026-04-12T14:00:45.000Z"
```
