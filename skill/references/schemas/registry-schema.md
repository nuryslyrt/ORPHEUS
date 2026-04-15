# Registry Schema

The Skill Registry is the index of all skills in an ORPHEUS system. It provides discovery, metadata, compatibility info, and versioning.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `system` | string | Yes | System name (matches system.yaml) |
| `version` | string | Yes | Registry version (semantic versioning) |
| `skills` | object | Yes | Contains orchestrator, experts, and workers sections |

### skills.orchestrator

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Orchestrator skill name |
| `path` | string | Yes | Relative path to SKILL.md from .orpheus/ root |
| `version` | string | Yes | Skill version |
| `contract` | string | Yes | Relative path to contract.yaml |

### skills.experts[] (Array)

Each entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Expert skill name |
| `path` | string | Yes | Relative path to SKILL.md |
| `version` | string | Yes | Skill version |
| `contract` | string | Yes | Relative path to contract.yaml |
| `tags` | string[] | No | Categorization tags |
| `compatible_workers` | string[] | No | Worker names this expert can use |

### skills.workers[] (Array)

Each entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Worker skill name |
| `path` | string | Yes | Relative path to SKILL.md |
| `version` | string | Yes | Skill version |
| `contract` | string | Yes | Relative path to contract.yaml |
| `tags` | string[] | No | Categorization tags |
| `model_preference` | string | No | Preferred model: `inherit` \| `opus` \| `sonnet` \| `haiku` |

## Example

```yaml
system: content-pipeline
version: "1.0.0"

skills:
  orchestrator:
    name: content-pipeline-orchestrator
    path: orchestrator/SKILL.md
    version: "1.0.0"
    contract: orchestrator/contract.yaml

  experts:
    - name: research-expert
      path: experts/research-expert/SKILL.md
      version: "1.0.0"
      contract: experts/research-expert/contract.yaml
      tags: [research, analysis]
      compatible_workers: [web-search-worker, data-extraction-worker]

    - name: writing-expert
      path: experts/writing-expert/SKILL.md
      version: "1.0.0"
      contract: experts/writing-expert/contract.yaml
      tags: [writing, content]
      compatible_workers: [grammar-check-worker, markdown-formatter-worker]

  workers:
    - name: web-search-worker
      path: workers/web-search-worker/SKILL.md
      version: "1.0.0"
      contract: workers/web-search-worker/contract.yaml
      tags: [search, web]
      model_preference: sonnet

    - name: grammar-check-worker
      path: workers/grammar-check-worker/SKILL.md
      version: "1.0.0"
      contract: workers/grammar-check-worker/contract.yaml
      tags: [validation, grammar]
      model_preference: haiku
```

## Validation Rules

1. `system` must match the `system.name` field in system.yaml
2. `version` must follow semantic versioning
3. Every `path` must point to an existing file on disk
4. Every `contract` path must point to an existing contract.yaml file
5. Every skill name must be unique across all sections (no duplicates)
6. `compatible_workers` entries must reference worker names that exist in skills.workers
7. `model_preference` if present must be one of: inherit, opus, sonnet, haiku
8. There must be exactly one orchestrator entry
9. There must be at least one expert entry
