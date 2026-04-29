# Assurance Claim Schema

An Assurance Claim is an explicit trust assertion the Auditor evaluates against an ORPHEUS system. The claim matrix is the list of claims that together define the system's safety case.

Claims live in one of two places:

- **Default catalog:** `references/claims/default-claims.yaml` (ships with the ORPHEUS skill). Used when a system has no override.
- **System override:** `.orpheus/claims.yaml` inside the generated system. Takes precedence over the default.

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Semantic version of the claim matrix format (currently `"1.0"`) |
| `system` | string | No | System name — optional in the default catalog, recommended in overrides |
| `extends_default` | boolean | No | If `true`, the system's claims are appended to the default catalog rather than replacing it. Default: `true`. |
| `claims` | array | Yes | One or more claim entries (see below) |

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

## validation_method Values

Ordered from strongest to weakest assurance. The Auditor is **prohibited from labeling up** — a claim declared `evidence` must never report status `proven`.

| Value | Meaning | Example |
|-------|---------|---------|
| `proof` | Mathematically decidable; a negative answer is a definitive failure | `workflow_termination` (DAG acyclicity) |
| `policy-as-code` | Mechanical rule check with a well-defined truth value | `tool_contract_soundness` (contract compatibility) |
| `evidence` | Artifact inspection — files exist, are well-formed, match expected shape | `artifact_integrity`, `configuration_validity` |
| `runtime` | Invariant that holds during live execution (Stage 2+; not used in Stage 1) | `no_worker_outside_allowlist_at_runtime` |
| `adversarial` | Exercised by red-team probing (Stage 3+; not used in Stage 1) | `prompt_injection_resistance` |

## checker Sub-Fields

| Field | Type | Description |
|-------|------|-------------|
| `worker` | string | Name of the worker to dispatch (e.g., `contract-compat-checker`, `dag-validator`). |
| `operation` | string | Operation or mode parameter for the worker. |
| `parameters` | object | Additional parameters passed to the checker. |

If `checker` is omitted, the Auditor performs the check directly by reading `evidence_source` and applying the claim-specific logic.

## Example

```yaml
version: "1.0"
system: content-pipeline
extends_default: true

claims:
  - id: workflow_termination
    statement: "The job dependency graph is a DAG and execution always terminates in bounded steps"
    validation_method: proof
    evidence_source:
      - registry.yaml
      - orchestrator/SKILL.md
    renewal_trigger: "Any job dependency edge added, removed, or retargeted"
    next_review_required_on: "registry.yaml:modified OR orchestrator/SKILL.md:routing_rules_changed"
    owner: surgeon
    risk_tier: critical
    tags: [correctness, structural]
    checker:
      worker: dag-validator
      operation: full_check

  - id: tool_contract_soundness
    statement: "Every producer/consumer contract chain has matching required fields with compatible types"
    validation_method: policy-as-code
    evidence_source:
      - "**/contract.yaml"
    renewal_trigger: "Any contract.yaml modified or new skill added with new contract"
    next_review_required_on: "**/contract.yaml:modified"
    owner: surgeon
    risk_tier: high
    tags: [correctness, composition]
    checker:
      worker: contract-compat-checker
      operation: scope_full

  - id: custom_system_claim_example
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

## Validation Rules

1. `id` must be unique across the entire claim matrix (default + override, after merge)
2. `id` must be snake_case (lowercase letters, numbers, underscores only)
3. `validation_method` must be one of the five enum values
4. `owner` must be one of: `doctor`, `surgeon`, `builder`, `user`
5. `risk_tier` must be one of: `critical`, `high`, `medium`, `low`
6. `evidence_source` must be non-empty; each entry must be a file path, glob pattern, or known logical source name
7. If `checker.worker` is specified, it must be a worker name known to the Auditor's available workers list

## Merge Semantics (default + override)

When `.orpheus/claims.yaml` is present and `extends_default: true` (the default):

1. Start with the default catalog
2. For each claim in the override:
   - If the `id` exists in the default, **replace** that claim with the override (full replacement, not field-level merge)
   - If the `id` is new, **append** it
3. The resulting merged matrix is what the Auditor evaluates

When `extends_default: false`, the override **replaces** the default catalog entirely. The system author takes full responsibility for claim coverage.

## Stage 1 Notes

- Stage 1 supports `validation_method` values `proof`, `policy-as-code`, and `evidence`. Claims declaring `runtime` or `adversarial` are accepted but the Auditor reports them as `unverified` with reason `"validation method not implemented in Stage 1"`.
- Stage 1 does not generate `.orpheus/claims.yaml` automatically. The Builder will do that in Stage 2.
- Stage 1 does not auto-propose new claims from execution patterns. That is a Stage 4 capability (learned invariants, earned confidence).
