# Assurance Claim Schema

An Assurance Claim is an explicit trust assertion the Auditor evaluates against an ORPHEUS system. The claim matrix is the list of claims that together define the system's safety case.

Claims are organized into **catalogs** — YAML files that group related claims. The Auditor merges catalogs based on each system's `extends` configuration.

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Semantic version of the claim matrix format (currently `"1.0"`) |
| `system` | string | No | System name — optional in catalogs, recommended in `.orpheus/claims.yaml` overrides |
| `extends` | string[] | No | Ordered list of catalog names to merge. Common values: `[default]` (standard), `[default, preview]` (forward visibility), `[]` (strict mode — no catalogs, only this file's `claims`). Default if absent: `[default]`. |
| `claims` | array | No | Custom claim entries unique to this system (highest precedence in merge order). |

## Claim Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier, snake_case (e.g., `workflow_termination`). Stable across runs — never renumber. |
| `statement` | string | Yes | What is being asserted, as a declarative natural-language sentence. |
| `validation_method` | enum | Yes | How this claim is checked. See values below. |
| `evidence_source` | array | Yes | One or more file path patterns or logical sources the evaluator reads. |
| `renewal_trigger` | string | Yes | Natural-language description of what change would require re-validation. |
| `next_review_required_on` | string | No | Machine-checkable form of the trigger (glob, file pattern, or keyword). Used by the Auditor to detect staleness automatically. |
| `owner` | enum | Yes | Which expert is responsible for fixing a failure: `doctor` \| `surgeon` \| `builder` \| `user`. |
| `risk_tier` | enum | Yes | `critical` \| `high` \| `medium` \| `low`. Drives report ordering and whether the Auditor blocks on failure. |
| `tags` | string[] | No | Categorization, e.g. `["authorization", "data-flow"]`. |
| `checker` | object | No | Which worker or procedure evaluates this claim (see below). If omitted, the Auditor evaluates inline. |
| `reason_unverified` | string | No | When this claim's `validation_method` is not yet implemented, this is the human-readable reason the Auditor displays. |

## validation_method Values

Ordered from strongest to weakest assurance. The Auditor is **prohibited from labeling up** — a claim declared `evidence` must never report status `proven`.

| Value | Meaning | Example |
|-------|---------|---------|
| `proof` | Mathematically decidable; a negative answer is a definitive failure | `workflow_termination` (DAG acyclicity) |
| `policy-as-code` | Mechanical rule check with a well-defined truth value | `tool_contract_soundness` (contract compatibility) |
| `evidence` | Artifact inspection — files exist, are well-formed, match expected shape | `artifact_integrity`, `configuration_validity` |
| `runtime` | Invariant that holds during live execution | `no_worker_outside_allowlist_at_runtime` |
| `adversarial` | Exercised by red-team probing | `prompt_injection_resistance` |

## checker Sub-Fields

| Field | Type | Description |
|-------|------|-------------|
| `worker` | string | Name of the worker to dispatch (e.g., `contract-compat-checker`, `dag-validator`). |
| `operation` | string | Operation or mode parameter for the worker. |
| `parameters` | object | Additional parameters passed to the checker. |

If `checker` is omitted, the Auditor performs the check directly by reading `evidence_source` and applying the claim-specific logic.

## Example

```yaml
# .orpheus/claims.yaml for a system that uses defaults plus one custom claim
version: "1.0"
system: content-pipeline
extends: [default]

claims:
  - id: writing_expert_uses_only_allowed_workers
    statement: "The writing-expert never delegates fact-checking to a worker outside its declared allowlist"
    validation_method: policy-as-code
    evidence_source:
      - experts/writing-expert/SKILL.md
      - registry.yaml
    renewal_trigger: "writing-expert SKILL.md or its available_workers list modified"
    next_review_required_on: "experts/writing-expert/SKILL.md:modified"
    owner: doctor
    risk_tier: high
    tags: [authorization, tool-scope]
```

## Catalog System

Catalogs live as YAML files at `{orpheus_skill}/references/claims/{name}.yaml`. The catalog name is the filename without the `.yaml` extension. Adding a new catalog is as simple as creating a new file in this directory — no code changes required.

### Built-in Catalogs

| Name | Purpose | Currently includes |
|------|---------|-------------------|
| `default` | Standard structural assurance | 7 claims covering registry, contracts, DAG, skills, routing, logs, config |
| `preview` | Forward-looking visibility for capabilities not yet validated | Claims using `runtime` and `policy-as-code` methods that the Auditor cannot yet evaluate; reported as `unverified` |

### Future Catalog Possibilities

The `extends` array makes ORPHEUS extensible to domain-specific assurance. Future catalogs the community might contribute include industry-specific compliance baselines (HIPAA, PCI), security postures (OWASP), and specialized validation contexts. Adding a new catalog requires no code changes — only a new YAML file conforming to the catalog schema.

## Validation Rules

1. `id` must be unique across the entire claim matrix (after all catalogs and the system override are merged)
2. `id` must be snake_case (lowercase letters, numbers, underscores only)
3. `validation_method` must be one of the five enum values
4. `owner` must be one of: `doctor`, `surgeon`, `builder`, `user`
5. `risk_tier` must be one of: `critical`, `high`, `medium`, `low`
6. `evidence_source` must be non-empty; each entry must be a file path, glob pattern, or known logical source name
7. If `checker.worker` is specified, it must be a worker name known to the Auditor's available workers list

## Merge Semantics

The Auditor builds the evaluated claim matrix from the system's `.orpheus/claims.yaml` (if present) following these rules:

1. Determine the `extends` list:
   - If `.orpheus/claims.yaml` is absent → `[default]`
   - If present with `extends` field → use that value
   - If present without `extends` field → `[default]` (backward compatible)

2. Load catalogs in `extends` order (left to right). For each catalog name `{name}`:
   - Read `{orpheus_skill}/references/claims/{name}.yaml`
   - Append all its claims to the working matrix
   - If a claim's `id` already exists in the working matrix, the new entry **replaces** the older one (later catalogs override earlier)

3. Append the system's custom `claims` array last. Custom claims have highest precedence — they override any default or preview claim with the same `id`.

4. The resulting matrix is what the Auditor evaluates.

### Edge Cases

| Case | Behavior |
|------|----------|
| `extends` field absent | Default to `[default]` (backward compatible) |
| `extends: []` (empty array) | Strict mode — only the system's own custom claims, no catalogs |
| `extends: []` AND `claims: []` | Empty matrix; Auditor reports "No claims defined; no validation performed" |
| `extends: [default, default]` | Idempotent — duplicate names load once, in first-occurrence order |
| `extends: [unknown_catalog]` | Error: catalog file not found; Auditor aborts with the list of available catalogs |
| Catalog file is malformed YAML | Error with file path; Auditor aborts |
| Catalog claim missing required field | Error naming the catalog, claim id, missing field; Auditor aborts |
| Same claim ID in multiple catalogs | Later in `extends` wins; system custom claims always win |
| Claim's `evidence_source` references file that doesn't exist | Status: `unverified`; reason explains the missing source; recommendation suggests updating the claim |

## Currently Supported

- The Auditor evaluates `proof`, `policy-as-code`, and `evidence` validation methods. Claims declaring `runtime` or `adversarial` are accepted but reported as `unverified` with reason "validation method not currently implemented".
- The Builder generates a stub `.orpheus/claims.yaml` for new systems. See `references/experts/builder.md` for details.
- Auto-proposing new claims from execution patterns is not currently implemented. System authors write custom claims by editing `.orpheus/claims.yaml`.

## Schema Versioning

The `version: "1.0"` field follows semantic versioning:

- **Minor bump (1.0 → 1.1):** Backward-compatible additions (new optional fields, new validation methods)
- **Major bump (1.x → 2.0):** Breaking changes (renaming/removing fields, changing required-field semantics)

When the Auditor encounters a claim matrix with a higher major version than it understands, it aborts with a helpful message rather than silently ignoring fields it doesn't recognize.
