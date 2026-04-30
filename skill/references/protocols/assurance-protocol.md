# ORPHEUS Assurance Protocol

How the Auditor loads a claim matrix, evaluates claims, computes renewal triggers, and emits an evidence package. This protocol implements the Provable Assurance capability — see `references/PROVABLE_ASSURANCE.md` for the framing and motivation.

## Loading the Claim Matrix

### Procedure

1. **Generate an audit ID** using the local copy of the ID generator:
   ```bash
   python3 .orpheus/scripts/generate-id.py a --base-path .orpheus
   ```

2. **Determine the system's `extends` configuration:**
   - If `.orpheus/claims.yaml` exists, read its `extends` field. Default to `[default]` if the field is absent.
   - If `.orpheus/claims.yaml` does NOT exist, use `extends: [default]`.
   - If `.orpheus/claims.yaml` exists with `extends: []`, the system uses only its own custom claims (strict mode).

3. **Scan available catalogs.** List `references/claims/*.yaml` files in the ORPHEUS skill install. Each file's basename (without `.yaml`) is a catalog name. Record this list as `available_catalogs` for the evidence package.

4. **For each catalog name in the system's `extends` array, in order:**
   - Read `{orpheus_skill_path}/references/claims/{name}.yaml`
   - If the file does not exist, ABORT with: "Catalog `{name}` not found in references/claims/. Known catalogs: `{list of available_catalogs}`."
   - Append all claims from the catalog. Later catalogs override earlier claims with the same `id`.

5. **Append the system's custom `claims` array last.** These have highest precedence — they override any default or preview claim with the same `id`.

6. **Validate the merged matrix.** See "Validation Error Format" below.

### Edge Cases

| Case | Behavior |
|---|---|
| `extends` field absent | Default to `[default]` |
| `extends: []` AND `claims: []` | Empty matrix. Report "No claims defined; no validation performed." Evidence package contains `claim_matrix_source.total_claim_count: 0`. Auditor does not crash. |
| `extends: [default, default]` | Idempotent — duplicate names load once, in first-occurrence order |
| `extends: [unknown_catalog]` | Abort with helpful error listing available catalogs |
| Catalog file is malformed YAML | Abort with file path; line number when YAML parser reports it |
| Catalog claim missing required field | Abort with catalog name, claim id, missing field |
| Same claim ID in multiple catalogs | Later in `extends` wins; system custom claims always win |
| Claim's `evidence_source` references file that doesn't exist | Status: `unverified`; reason names the missing file; recommendation suggests updating |

### Validation Error Format

When the matrix or any catalog fails validation, produce errors with this structure:

```
Claim matrix validation failed:
  File: {file_path}
  Line: {line_number — when YAML parser reports it}
  Issue: {what is wrong}
  Required: {what should be there}
  Suggestion: {actionable fix when obvious}
```

Concrete example:

```
Claim matrix validation failed:
  File: .orpheus/claims.yaml
  Line: 12
  Issue: Claim 'my_custom_claim' missing required field 'validation_method'
  Required: One of: proof, policy-as-code, evidence, runtime, adversarial
  Suggestion: Add `validation_method: policy-as-code` if the claim checks
              a mechanical rule, or `evidence` for artifact inspection.
```

LOG: `matrix_loaded` — record which catalogs were merged (`extends` value), `available_catalogs` scan result, `has_system_override`, custom claim count, total claim count, which (if any) catalogs were unknown.

## Evaluating Claims

Each claim corresponds to exactly one validation procedure. Run the check, then record the result in claim terms.

### Default Catalog Claims

#### Claim: artifact_integrity

**Dispatch registry-updater** with operation="scan".

Additionally verify yourself:
- Every skill entry in registry.yaml has a `path` that points to an existing SKILL.md file
- Every skill entry has a `contract` that points to an existing contract.yaml file
- No skill directories exist on disk that aren't listed in the registry (orphaned)
- All skill names are unique across orchestrator, experts, and workers sections
- Version strings follow semantic versioning

Record:
- Collect file paths read and their sha256 hashes → evidence items of type `file_hash`
- Status: `attested` if all entries valid; retain status but add exceptions for orphans/missing files
- Exception severities: orphaned files = `advisory`; missing files = `blocker`

#### Claim: tool_contract_soundness

**Dispatch contract-compat-checker** with scope="full".

Record:
- Evidence item type `contract_chain_check`, checker `contract-compat-checker`, result_summary from worker output
- Status: `checked` (validation method is `policy-as-code`)
- Exceptions: unused output fields → `advisory`; missing required fields or type mismatches → `blocker`

#### Claim: workflow_termination

**Dispatch dag-validator** with the system path.

Record:
- Evidence item type `dag_snapshot`, source `registry.yaml`, hash of registry.yaml, result_summary from worker
- Status: `proven` — the ONE claim that earns the `proof` label because DAG acyclicity is mathematically decidable
- Exceptions: orphaned jobs → `warning`; cycles or dangling references → `blocker`

#### Claim: skill_definition_completeness

Perform this check directly (no worker needed). For each SKILL.md in the system:

- [ ] Frontmatter has required fields: name, description, type, version
- [ ] Frontmatter has `orpheus.system` matching the system name
- [ ] Expert SKILL.md files have an "Execution Protocol" section (or similar multi-phase protocol)
- [ ] Expert SKILL.md files have a "Quality Gate" section
- [ ] All SKILL.md files have a "Logging Protocol" section
- [ ] Worker SKILL.md files have a "Task Protocol" section
- [ ] Worker SKILL.md files have an "Output Format" section
- [ ] Worker SKILL.md files have a "Constraints" section
- [ ] No SKILL.md exceeds 500 lines (warning threshold)

Record:
- Evidence item type `skill_md_audit`, one per skill, with hash of the SKILL.md file and a list of sections found
- Status: `checked` (policy-as-code — mechanical rule applied to file contents)
- Exceptions: missing non-critical section → `advisory`; missing critical section → `blocker`; line count warning → `warning`

#### Claim: routing_totality

Perform this check directly. Read the orchestrator SKILL.md:

- [ ] Routing rules exist for every expert listed in the registry
- [ ] A default/catch-all routing rule exists (or explicit handling for unmatched requests)
- [ ] No ambiguous routing patterns (two rules could match the same input)
- [ ] Available experts table matches the registry's expert list
- [ ] Available workers summary is present

Record:
- Evidence item type `routing_coverage_map`, containing which expert → which routing rule(s)
- Status: `checked`
- Exceptions: missing catch-all → `warning`; experts with no routing rule → `blocker`

#### Claim: observability_integrity

**Dispatch log-analyzer** with operation="health_check".

Additionally verify:
- `.orpheus/logs/` directory exists
- `build/` and `runtime/` subdirectories exist
- For recent executions: check if assembled views exist (timeline, decisions, errors)

Record:
- Evidence item type `log_inspection`, with list of executions checked and their assembly status
- Status: `attested` (method is `evidence`)
- Exceptions: executions missing assembled views → `warning`; missing or corrupt log structure → `blocker`

#### Claim: configuration_validity

Perform this check directly. Read `.orpheus/system.yaml`:

- [ ] `system.name` exists and is non-empty
- [ ] `orchestrator.strategy` is one of: sequential, parallel, adaptive
- [ ] `orchestrator.max_retries` is a non-negative integer
- [ ] `orchestrator.timeout_seconds` is a positive number
- [ ] `orchestrator.escalation` is one of: user, skip, fallback
- [ ] `logging.level` is one of: trace, debug, info, warn, error
- [ ] `logging` boolean fields are actual booleans
- [ ] `.orpheus/scripts/` directory exists with runtime scripts

Record:
- Evidence item type `config_snapshot`, hash of system.yaml, list of scripts present in scripts/
- Status: `attested`
- Exceptions: using defaults for optional fields → `advisory`; invalid required values or missing scripts → `blocker`

### Claims with Unimplemented Validation Methods

For claims with `validation_method` of `runtime` or `adversarial`:

- Record status: `unverified`
- Evidence: empty list
- Exceptions: empty list
- `reason` field: `"Validation method '{method}' is not currently implemented"`

This is intentional. The evidence package should surface what ORPHEUS does NOT yet validate, not hide it from the reviewer.

### Custom Claims

If the matrix contains claims not in the default catalog:

1. Read the claim's `checker` field.
2. If a worker is specified: dispatch it with the parameters.
3. If no checker: attempt direct evaluation based on `evidence_source` (read files, verify existence and well-formedness at minimum).
4. If evaluation cannot be performed: status `unverified`, reason `"No checker defined and direct evaluation not possible for this claim"`.

## Computing Renewal Triggers

Compute which claims need re-validation because their inputs changed since the previous audit.

1. **If no previous evidence package exists** (first audit of this system): `renewal_triggers_active = []`. Skip the rest of this phase.

2. **For each claim evaluated:**
   - Find the same claim in the previous evidence package by `id`.
   - For each evidence item with a `hash` field: compare against the previous run's hash for the same source file.
   - For file paths in `evidence_source` that don't appear in the current evidence items (because the claim was skipped or the file didn't exist): check mtime against the previous audit's `audited_at`.
   - If any source file changed after the previous audit, add a renewal trigger entry:
     ```yaml
     claim_id: "{claim.id}"
     reason: "{specific file} modified {mtime}, after last audit at {previous.audited_at}"
     recommended_action: "re-run audit"
     ```

3. LOG: `renewal_triggers_computed` — count of claims flagged, which files changed.

## Emitting the Evidence Package

After evaluation and renewal trigger computation:

1. **Aggregate all check results.** For each claim, record: claim id, status, evidence items, exceptions, renewal trigger metadata copied from the matrix.

2. **Emit the evidence package** to `.orpheus/logs/build/{audit_id}/evidence-package.yaml` following the schema in `references/schemas/evidence-package-schema.md`. This is the machine-readable artifact the reviewer takes away from the audit.

3. The package's `claim_matrix_source` field captures provenance:
   ```yaml
   claim_matrix_source:
     extends: [default]                       # what's enabled
     available_catalogs: [default, preview]   # what's installed
     has_system_override: true                # whether .orpheus/claims.yaml exists
     custom_claim_count: 0                    # claims from system override
     total_claim_count: 7                     # sum after merge
   ```

## The "No Labeling Up" Rule

The Auditor is **prohibited from labeling up** — a claim's reported status must not exceed its declared validation method's strength.

| Validation method | Permitted status (positive) |
|---|---|
| `proof` | `proven` |
| `policy-as-code` | `checked` |
| `evidence` | `attested` |
| `runtime` | (currently always `unverified`) |
| `adversarial` | (currently always `unverified`) |

Any validation method may produce `unverified` (when the validator could not run) or `failed` (when the check ran and found violations).

### Why This Rule Exists

Conflating assurance strengths is the specific failure mode the Provable Assurance framework exists to prevent. A claim declared `evidence` reporting `proven` would mislead a reviewer into thinking the property is mathematically guaranteed when it was only verified by artifact inspection.

The hierarchy from strongest to weakest:
- `proven` (mathematically decidable)
- `checked` (mechanical rule with truth value)
- `attested` (artifact inspection)

Reviewers reading `attested` should not assume `checked`. Reviewers reading `checked` should not assume `proven`. The Auditor enforces this in both the YAML output (`status` field never exceeds declared method) and the display table (Status column shows the achieved level explicitly).
