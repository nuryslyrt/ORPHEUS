# Job Definition Schema

A Skill Job is a declarative unit of work created by the orchestrator and consumed by an expert.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string | Yes | Unique identifier within execution (kebab-case, e.g., `research-quantum`) |
| `title` | string | Yes | Human-readable description of the job |
| `status` | enum | Yes | `pending` \| `dispatched` \| `running` \| `completed` \| `failed` |
| `assigned_expert` | string | Yes | Name of the expert skill assigned to this job |
| `priority` | number | No | 1 (highest) to 10 (lowest). Default: 5 |
| `dependencies` | string[] | No | Job IDs this job must wait for. Default: [] |
| `retry_count` | number | No | Current retry count. Default: 0 |
| `input` | object | Yes | Arbitrary input data. Must conform to the assigned expert's contract.input |
| `expected_output` | object | Yes | What the orchestrator expects back (see sub-fields below) |
| `metadata` | object | Auto | Timestamps and duration (auto-generated during execution) |

### expected_output Sub-Fields

| Field | Type | Description |
|-------|------|-------------|
| `format` | enum | `yaml` \| `json` \| `markdown` \| `text` |
| `fields` | string[] | Required field names in the result |

### metadata Sub-Fields

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | string | ISO 8601 timestamp when job was created |
| `dispatched_at` | string | ISO 8601 timestamp when job was dispatched to expert |
| `completed_at` | string | ISO 8601 timestamp when job finished |
| `duration_seconds` | number | Total execution time in seconds |

## Example

```yaml
job_id: "research-market-trends"
title: "Research current market trends in AI"
status: pending
assigned_expert: research-expert
priority: 1
dependencies: []
retry_count: 0
input:
  topic: "AI market trends 2026"
  depth: deep
  constraints:
    max_sources: 10
    recency: "last 6 months"
expected_output:
  format: yaml
  fields: [findings, sources, confidence]
metadata:
  created_at: "2026-04-12T14:00:00.000Z"
  dispatched_at: ""
  completed_at: ""
  duration_seconds: 0
```

## Validation Rules

1. `job_id` must be non-empty, kebab-case (lowercase letters, numbers, hyphens only)
2. `status` must be one of the 5 enum values
3. `assigned_expert` must match a skill name in the registry's experts list
4. `dependencies` must reference existing job IDs (no self-references, no cycles)
5. `priority` if present must be integer 1-10
6. `retry_count` if present must be non-negative integer
7. `expected_output.format` must be one of the 4 enum values
8. `expected_output.fields` must be a non-empty array of strings

## Status Transitions

```
pending → dispatched → running → completed
                         │
                         └──→ failed → (retry?) → pending
```
