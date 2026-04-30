# Evidence Package Schema

The Evidence Package is the Auditor's output artifact for Stage 1 of Provable Assurance. It maps every claim in the matrix to the concrete evidence that currently supports it, records any open exceptions, and identifies which claims need re-validation because their inputs changed.

An evidence package is written to `.orpheus/logs/build/{audit_id}/evidence-package.yaml` after every audit. One file per audit run; audits are never mutated retroactively.

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audit_id` | string | Yes | Audit operation ID (e.g., `a012`) |
| `system` | string | Yes | System name, read from `system.yaml` |
| `audited_at` | string | Yes | ISO 8601 timestamp with milliseconds |
| `auditor_version` | string | Yes | Version of the Auditor expert that produced this package |
| `claim_matrix_source` | object | Yes | Records exactly which catalogs were merged and whether a system override was applied (see below) |
| `claim_matrix_version` | string | Yes | `version` field from the evaluated claim matrix |
| `overall_status` | enum | Yes | `healthy` \| `warnings` \| `degraded` \| `broken` |
| `health_score` | number | Yes | 0.0 to 1.0 (same calculation as pre-Stage-1 Auditor) |
| `claims` | array | Yes | One entry per claim evaluated (see below) |
| `renewal_triggers_active` | array | Yes | Claims currently requiring re-validation because their inputs changed since last audit (see below). May be empty. |
| `recommendations` | array | Yes | Actionable items from the Auditor, unchanged from pre-Stage-1 format |

## claim_matrix_source Sub-Fields

Records the provenance of the evaluated claim matrix so reviewers know exactly which catalogs and which system override contributed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `extends` | string[] | Yes | The resolved `extends` list — which catalogs were merged in order |
| `available_catalogs` | string[] | Yes | All catalogs installed in the ORPHEUS skill (scan of `references/claims/*.yaml`). Reviewers see opt-in catalogs that exist but weren't enabled. |
| `has_system_override` | boolean | Yes | Whether `.orpheus/claims.yaml` exists |
| `custom_claim_count` | number | Yes | Count of claims contributed by the system's `.orpheus/claims.yaml` `claims` array |
| `total_claim_count` | number | Yes | Total claims after merge (catalogs + custom) |

Example:

```yaml
claim_matrix_source:
  extends: [default]
  available_catalogs: [default, preview]
  has_system_override: true
  custom_claim_count: 0
  total_claim_count: 7
```

A reviewer reading this sees: "Standard 7-claim assurance, no custom claims, but the `preview` catalog is available if forward visibility is needed."

## Claim Result Entry

One of these per claim in the evaluated matrix.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Matches `claims[].id` from the claim matrix |
| `statement` | string | Yes | Copied from the matrix for standalone readability |
| `validation_method` | enum | Yes | Copied from the matrix |
| `status` | enum | Yes | Result of this audit: `proven` \| `checked` \| `attested` \| `unverified` |
| `evidence` | array | Yes | Concrete evidence items gathered (see below). May be empty when `status=unverified`. |
| `exceptions` | array | Yes | Open issues discovered. May be empty. |
| `renewal_trigger` | string | Yes | Copied from the matrix |
| `next_review_required_on` | string | No | Copied from the matrix when present |
| `owner` | enum | Yes | Copied from the matrix |
| `risk_tier` | enum | Yes | Copied from the matrix |
| `reason` | string | No | Only populated when `status=unverified`, explaining why |

## status Values

The strength hierarchy — the Auditor is **never allowed to label up**.

| Status | When used |
|--------|-----------|
| `proven` | Claim has `validation_method=proof` AND the proof procedure returned positive |
| `checked` | Claim has `validation_method=policy-as-code` AND all rules passed |
| `attested` | Claim has `validation_method=evidence` AND all evidence items were well-formed |
| `unverified` | The validator could not run, the method is not implemented in this stage, or evaluation was skipped. **NOT the same as failure** — failure is represented by `exceptions` and is reflected in `overall_status`. |

A claim whose checker ran but returned failures carries the status corresponding to its method (`proven`/`checked`/`attested`) with a populated `exceptions` array. `unverified` is reserved for inability-to-evaluate.

## Evidence Item Sub-Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Category, e.g. `dag_snapshot`, `contract_chain_check`, `file_hash`, `log_inspection` |
| `source` | string | Yes | Relative path or logical source name |
| `hash` | string | No | `sha256:...` of the source file when applicable. Required for `file_hash`-type evidence. |
| `captured_at` | string | Yes | ISO 8601 timestamp when this evidence item was collected |
| `checker` | string | No | Worker or procedure that produced this evidence (e.g., `dag-validator`) |
| `result_summary` | string | No | One-line summary of what the checker concluded |
| `detail` | object | No | Free-form structured data specific to the evidence type |

## Exception Sub-Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique within this claim, snake_case |
| `severity` | enum | Yes | `advisory` \| `warning` \| `blocker` |
| `description` | string | Yes | What the exception is |
| `recommended_action` | string | No | What the owner expert should do |
| `related_evidence` | string[] | No | Indices or types of related evidence items |

## Renewal Trigger Entry

One per claim where the inputs changed since the last audit.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | string | Yes | Matches `claims[].id` |
| `reason` | string | Yes | What changed (e.g., `"experts/writing-expert/SKILL.md modified 2026-04-28T09:14Z, after last audit at 2026-04-27T22:01Z"`) |
| `recommended_action` | string | Yes | `"re-run audit"` \| `"dispatch surgeon"` \| etc. |

`renewal_triggers_active` is computed by comparing file mtimes (or hashes if mtimes are unreliable) against the timestamps in the most recent previous evidence package. On the first audit of a system, this field is `[]`.

## Full Example

```yaml
audit_id: a012
system: content-pipeline
audited_at: 2026-04-29T10:12:03.000Z
auditor_version: "1.1.0"
claim_matrix_source:
  extends: [default]
  available_catalogs: [default, preview]
  has_system_override: true
  custom_claim_count: 0
  total_claim_count: 7
claim_matrix_version: "1.0"
overall_status: warnings
health_score: 0.79

claims:
  - id: workflow_termination
    statement: "The job dependency graph is a DAG and execution always terminates in bounded steps"
    validation_method: proof
    status: proven
    evidence:
      - type: dag_snapshot
        source: registry.yaml
        hash: sha256:3f2a9e11c4d6b8870a2f15ed9c4e2b1f8a6d03c5b2e7f1a8d94b6e2c5d7f9a0b
        captured_at: 2026-04-29T10:12:01.000Z
        checker: dag-validator
        result_summary: "no cycles, no dangling references, 4 batches computed"
    exceptions: []
    renewal_trigger: "Any job dependency edge added, removed, or retargeted"
    next_review_required_on: "registry.yaml:modified OR orchestrator/SKILL.md:routing_rules_changed"
    owner: surgeon
    risk_tier: critical

  - id: tool_contract_soundness
    statement: "Every producer/consumer contract chain has matching required fields with compatible types"
    validation_method: policy-as-code
    status: checked
    evidence:
      - type: contract_chain_check
        source: "**/contract.yaml"
        captured_at: 2026-04-29T10:12:02.000Z
        checker: contract-compat-checker
        result_summary: "all chains compatible, 2 unused output fields (advisory)"
    exceptions:
      - id: unused_field_research_expert_sources
        severity: advisory
        description: "research-expert produces 'sources' in output but no downstream expert consumes it"
        recommended_action: "Consider removing from contract or adding a downstream consumer"
    renewal_trigger: "Any contract.yaml modified or new skill added with new contract"
    owner: surgeon
    risk_tier: high

  - id: information_flow_boundaries
    statement: "Workers cannot be dispatched by experts not listed as their caller in the registry"
    validation_method: runtime
    status: unverified
    evidence: []
    exceptions: []
    renewal_trigger: "Any registry change affecting available_workers"
    owner: doctor
    risk_tier: medium
    reason: "Validation method 'runtime' is not implemented in Stage 1. Claim reserved for Stage 2+."

renewal_triggers_active:
  - claim_id: skill_definition_completeness
    reason: "experts/writing-expert/SKILL.md modified 2026-04-28T09:14Z, after last audit at 2026-04-27T22:01Z"
    recommended_action: "re-run audit"

recommendations:
  - priority: medium
    target_expert: doctor
    action: "Re-run audit to refresh skill_definition_completeness evidence for writing-expert"
    claim: skill_definition_completeness
```

## Reproducibility Guarantee

An evidence package is **reproducible** for a given system state. If the system is unchanged between two audits, the generated packages must be **byte-identical in the claim-result portion** with the exceptions of:

- `audit_id` (sequence number increments)
- `audited_at` and `evidence[].captured_at` (timestamps)
- `renewal_triggers_active` (empty on both runs if the system didn't change)

`evidence[].hash` for file-based evidence MUST match across runs when the source file is unchanged. This is the testable property that enables the Reproducibility Test described in `PROVABLE_ASSURANCE.md`.

## Validation Rules

1. Every claim in the matrix MUST have a corresponding entry in `claims[]` — no silent drops
2. A claim with `validation_method=proof` MUST have status `proven` or `unverified`, never `checked` or `attested` (that would be labeling up)
3. Similarly, `policy-as-code` MUST be `checked` or `unverified`; `evidence` MUST be `attested` or `unverified`
4. `status=unverified` MUST include a `reason` field
5. `overall_status` derives from the exception set: `healthy` (no exceptions), `warnings` (advisory/warning only), `degraded` (1-2 blocker exceptions), `broken` (3+ blocker exceptions or any unverified critical claim)
6. `health_score` uses the pre-Stage-1 formula: average of per-check scores where pass=1.0, warn=0.5, fail=0.0

## Stage 1 Limitations (documented)

- `information_flow_boundaries` and similar runtime claims are reserved as `unverified` placeholders to make Stage 2 scope visible in Stage 1 output. This is intentional — the evidence package should tell the reviewer what is *not* yet validated, not hide it.
- Hash-based evidence uses sha256 of the file's on-disk content at `captured_at` time. Canonical form normalization (e.g., YAML re-serialization) is not performed in Stage 1. Whitespace-only edits to source files will therefore trigger renewal, which is the safe default.
