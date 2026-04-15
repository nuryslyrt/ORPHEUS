# Log Entry Schema

Every log entry in ORPHEUS follows this unified schema. Entries are stored as individual YAML files (entry-001.yaml, entry-002.yaml, etc.) in the skill's log directory.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique entry ID (e.g., "log-e001-0042") |
| `timestamp` | string | Yes | ISO 8601 with milliseconds (e.g., "2026-04-12T14:00:05.123Z") |
| `execution_id` | string | Yes | Execution or build ID (e.g., "e001", "b002") |
| `source` | object | Yes | Which skill generated this entry (see sub-fields) |
| `level` | enum | Yes | `trace` \| `debug` \| `info` \| `warn` \| `error` \| `fatal` |
| `category` | enum | Yes | `action` \| `decision` \| `state_change` \| `delegation` \| `result` \| `error` \| `lifecycle` \| `contract` \| `system` |
| `event` | string | Yes | Machine-readable event name (e.g., "job.dispatched", "skill.completed") |
| `summary` | string | Yes | Human-readable one-line summary |
| `detail` | object | No | Event-specific structured data (varies by category) |
| `decision` | object | No | Present ONLY for category=decision entries (see sub-fields) |
| `correlation` | object | No | Links this entry to related entries (see sub-fields) |

### source Sub-Fields

| Field | Type | Description |
|-------|------|-------------|
| `skill_name` | string | Name of the skill that generated this entry |
| `skill_type` | enum | `orchestrator` \| `expert` \| `worker` \| `builder` |
| `job_id` | string | Job context (null for orchestrator-level entries) |
| `parent_skill` | string | The skill that invoked this one (null for orchestrator) |

### decision Sub-Fields (only when category=decision)

| Field | Type | Description |
|-------|------|-------------|
| `question` | string | What was being decided |
| `options_considered` | string[] | Alternatives evaluated (at least 2) |
| `chosen` | string | The option that was selected |
| `reasoning` | string | WHY this option was chosen (1-3 sentences) |
| `confidence` | number | Self-assessed confidence, 0.0 to 1.0 |

### correlation Sub-Fields

| Field | Type | Description |
|-------|------|-------------|
| `parent_log_id` | string | ID of the log entry that caused this one |
| `batch_id` | string | Shared ID for entries in the same parallel batch |
| `trace_path` | string | Full path: e.g., "orchestrator > research-expert > web-search-worker" |

## Example

```yaml
id: "log-e001-005"
timestamp: "2026-04-12T14:00:04.000Z"
execution_id: "e001"
source:
  skill_name: research-expert
  skill_type: expert
  job_id: research-quantum
  parent_skill: null
level: info
category: decision
event: "expert.complexity_assessment"
summary: "Job requires workers — topic too broad for direct execution"
decision:
  question: "Can this job be handled directly or does it need workers?"
  options_considered:
    - "direct execution"
    - "delegate to workers"
  chosen: "delegate to workers"
  reasoning: "Quantum computing is a broad topic requiring parallel searches across multiple sub-domains. Estimated 5+ search queries needed."
  confidence: 0.88
correlation:
  parent_log_id: "log-e001-003"
  batch_id: "batch-1"
  trace_path: "orchestrator > research-expert"
```

## Validation Rules

1. `id` must be unique within the execution
2. `timestamp` must be valid ISO 8601 with timezone
3. `level` must be one of the 6 enum values
4. `category` must be one of the 9 enum values
5. `decision` block is required when category=decision, forbidden otherwise
6. `decision.options_considered` must have at least 2 entries
7. `decision.confidence` must be between 0.0 and 1.0
8. `source.skill_type` must be one of the 4 enum values

## Standard Events

| Event | Category | When |
|-------|----------|------|
| `skill.loaded` | lifecycle | Skill definition loaded into context |
| `skill.invoked` | lifecycle | Skill starts executing |
| `skill.completed` | lifecycle | Skill finishes successfully |
| `skill.errored` | lifecycle | Skill encounters a failure |
| `job.dispatched` | delegation | Orchestrator sends job to expert |
| `worker.dispatched` | delegation | Expert sends task to worker |
| `job.result_received` | result | Orchestrator receives expert's result |
| `job.status_changed` | state_change | Job transitions between statuses |
| `contract.validated` | contract | Contract check completed |
| `tool.invoked` | action | A tool (WebSearch, Bash, etc.) was used |
