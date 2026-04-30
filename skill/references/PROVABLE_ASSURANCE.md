# Provable Assurance for ORPHEUS Systems

## What This Is

ORPHEUS systems are agentic: they decompose user intent into jobs, dispatch work to experts, invoke tools through workers, and modify state on behalf of the user. The trust question for systems like this is not "does the code compile" — it is "can we continuously prove the system is behaving within approved bounds, with evidence?" This concern is well-developed in the agentic safety literature; the framework presented here aligns with the approach described in Schwartz (2026), *Provable Assurance for Agentic Systems*, while standing on its own merits.

The Provable Assurance capability reframes the **Auditor** around that question. It does not add a new skill, a new runtime, or new dependencies. It adds a vocabulary, an input file, and an output artifact:

- **Vocabulary:** the seven existing structural checks are promoted to named *assurance claims*, each with an explicit validation method, evidence source, and renewal trigger.
- **Input:** an optional `.orpheus/claims.yaml` lets a system author declare custom claims. If absent, the Auditor uses a default claim catalog shipped with the skill.
- **Output:** alongside the health report, the Auditor now emits an `evidence-package.yaml` — a signed-style artifact that maps every required claim to the concrete evidence that currently supports it, any open exceptions, and what would cause the claim to need re-validation.

This is a framing change. The Auditor still reads the same files and runs the same validations it did before. The difference is that "the DAG has no cycles" becomes the claim *workflow_termination*, validated by method `proof`, with renewal trigger *"any change to the dependency graph or a new job added."* That reframing is what turns an ORPHEUS audit into a safety-case-style attestation rather than a CI-style pass/fail.

Stage 2 (planned, not part of this change) adds two new checks — decision consistency across logs and claim coverage — and a first-class `.orpheus/claims.yaml` authored by the Builder when a new system is created.

## Why ORPHEUS Needs This

Three reasons, in order of concreteness.

**1. ORPHEUS is already producing most of the evidence, but nothing consumes it as evidence.**

Every ORPHEUS skill is required to log decisions with `question / options_considered / chosen / reasoning / confidence` (see `PRINCIPLES.md` Principle 6). Every error is wrapped across all three levels rather than flattened (Principle 8). Every worker invocation leaves a trace. That is the *observability substrate* the whitepaper names as a precondition for provable assurance — ORPHEUS just wasn't framing it that way. Without the claim matrix, the logs are a debugging aid; with the claim matrix, they become attestations linked to specific trust assertions.

**2. The current Auditor report does not answer the questions a reviewer actually asks.**

The whitepaper's "What Good Looks Like" section lists six questions a mature assurance program must be able to answer quickly:

- What critical properties have been proven, strongly verified, or continuously monitored?
- What assumptions does the system rely on?
- What tools can it call, with what scope, on whose authority?
- What sensitive data can influence decisions or be exposed by actions?
- What changed since the last approval decision?
- Which assurances remain valid, and which must be re-established?

The pre-Stage-1 Auditor produces a 0–1 score and seven check results. It answers *none* of those questions directly. The evidence package answers the first, second, fifth, and sixth; claim statements answer the third and fourth when a system author writes them.

**3. Without renewal triggers, every ORPHEUS audit is an expiring snapshot with no expiration date written on it.**

The whitepaper is blunt: "Point-in-time approval is a fiction for systems whose models, tools, dependencies, policies, and operating context change continuously." An ORPHEUS system whose registry changed after the last audit is in exactly that situation, and nothing in the current Auditor tells the user *which claims those changes invalidated*. Stage 1 makes the trigger explicit per claim, so the Auditor can report "authorization_boundaries needs re-validation: `experts/writing-expert/SKILL.md` modified after last audit."

## On Staging

This document organizes future capabilities into numbered "stages" — Stage 1 (currently shipped), Stage 2, Stage 3, Stage 4. The numbering is conceptual, not committed:

- Stages group related capabilities that share design assumptions or implementation infrastructure (for example, runtime and adversarial validation share the need for live execution under instrumented conditions).
- Stage numbering does NOT imply a release sequence. ORPHEUS may ship Stage 3 capabilities before Stage 2 if user demand favors them. Stages may merge, split, be deprecated, or have new ones discovered as the framework evolves.
- "Stage 1" describes what shipped. Other stages describe possibilities, not promises.

Operational documentation (the Auditor's instructions, schema references, error messages, the default claim catalog) deliberately avoids stage numbering. Those documents reflect current state and known capabilities, not roadmap.

## What Changes in the Auditor

| Before Stage 1 | After Stage 1 |
|:---|:---|
| 7 structural checks | 7 claims (same evidence, PAAS framing) |
| Health score (0–1.0) | Health score + assurance status per claim |
| Recommendations keyed to Doctor/Surgeon | Recommendations + renewal triggers + evidence gaps |
| No external output artifact | `evidence-package.yaml` written to `.orpheus/logs/build/{audit_id}/` |
| Claims are implicit | Claims are explicit, from `.orpheus/claims.yaml` or the default catalog |

Every pre-Stage-1 capability is preserved. A system with no `.orpheus/claims.yaml` gets the default catalog and a report that still contains the old score and the old recommendations — plus the new evidence package.

## When the Capability Activates

Stage 1 is an **Auditor-scoped** capability. It only executes when the user's intent routes to the Auditor. The meta-orchestrator's other routes — Builder, Runner, Doctor, Surgeon — do not read the claim matrix, evaluate claims, or emit evidence packages.

This is deliberate. The whitepaper's "renewable approval" principle says assurance must be triggered by material change, and Stage 1 keeps that trigger explicit: the user runs the Auditor when they want an evidence package. No background task, no auto-invocation, no hidden work on other routes. That conservative posture is the right one for Stage 1 because it makes the capability's effects observable and its failure modes localizable.

The consequence is that running Builder, Runner, Doctor, or Surgeon alone produces no Stage 1 output. The user must follow up with an audit to refresh the evidence package after any material change.

| Route | Trigger phrases | Stage 1 active? | Why |
|:---|:---|:---|:---|
| **Builder** | "build a system", "create a pipeline" | No | Builder creates systems; it doesn't evaluate claims against them. |
| **Runner** | "run the pipeline", "execute on {URL}" | No | Runner executes; the claim matrix has no runtime role in Stage 1. |
| **Auditor** | "audit", "validate", "check health", "verify", "scan" | **Yes** | The only route that loads the matrix, evaluates claims, and emits evidence. |
| **Doctor** | "why did X fail", "debug", "fix the error" | No | Doctor reads logs to diagnose specific failures. No claim evaluation. |
| **Surgeon** | "add an expert", "restructure", "split job" | No | Surgeon mutates structure. Stage 1 does not auto-audit after surgery — the user triggers the Auditor explicitly. |

### Future Work: Reducing Friction

Per the staging note above, the following are conceptual groupings, not committed deliverables in sequence.

Keeping activation explicit in Stage 1 is the conservative choice, but it means evidence packages drift out of date as the user operates through other routes. Stage 2 and beyond can close that gap without violating the renewable-approval principle, because each of the following still preserves the "material change triggers assurance work" contract — they just remove the need for the user to type the word "audit":

- **Auto-audit after Surgeon.** When the Surgeon completes a structural change (add/remove/rename/split/merge/restructure), the meta-orchestrator auto-chains an Auditor run so the evidence package reflects the post-surgery state immediately. This is the whitepaper's "automated re-evaluation when the environment changes" applied to the one route that most obviously changes the environment.
- **Pre-flight audit on Runner.** Before executing, the Runner reads the most recent evidence package. If `overall_status = broken` or any `critical`-tier claim is `unverified`, it warns the user and asks to proceed. Cheap, non-blocking, keeps assurance in the loop without blocking hot-path execution.
- **Evidence-package staleness warning on any route.** If the latest evidence package is older than the oldest file in `.orpheus/`, the meta-orchestrator adds a one-line "your evidence package is stale, run an audit" to any response. Nearly free, and keeps stale assurance visible without inventing unsolicited work.

Each of these requires edits to the meta-orchestrator `SKILL.md` and, for the Surgeon hand-off, a small change to the Surgeon's Phase 6 report. None are in Stage 1 scope. They are called out here so that the present tradeoff — explicit activation at the cost of potential staleness — is understood as a staging decision rather than a permanent constraint.

## Mapping the Seven Checks to Claims

Each default claim keeps one-to-one correspondence with an existing check, so the change is reversible and auditable. The full catalog lives in `references/claims/default-claims.yaml`; a sketch:

| Old check | Claim id | Validation method | Renewal trigger |
|:---|:---|:---|:---|
| Registry Integrity | `artifact_integrity` | evidence | `registry.yaml` or any referenced file changes |
| Contract Compatibility | `tool_contract_soundness` | policy-as-code | any `contract.yaml` modified |
| DAG Validity | `workflow_termination` | proof | any dependency edge added/removed |
| Skill Quality | `skill_definition_completeness` | policy-as-code | any SKILL.md modified |
| Orchestrator Coverage | `routing_totality` | policy-as-code | orchestrator SKILL.md or registry expert list changes |
| Log Health | `observability_integrity` | evidence | new execution without assembled views |
| Configuration Validity | `configuration_validity` | evidence | `system.yaml` modified |

The five validation methods follow the whitepaper directly:

- **proof** — mathematically checkable (DAG acyclicity is the canonical example in ORPHEUS)
- **policy-as-code** — machine-executable rules (contract compatibility, routing coverage)
- **evidence** — artifact inspection (files exist, hashes match, schemas validate)
- **runtime** — invariants that must hold during execution (Stage 2+; not yet claimed)
- **adversarial** — exercised by red-team-style probing (Stage 3+; not in scope)

Marking DAG validity as `proof` is deliberate: it is the one thing in ORPHEUS that is actually mathematically decidable, and the whitepaper's framing earns its strongest assurance label. Everything else in Stage 1 is `policy-as-code` or `evidence`, and the Auditor is required not to conflate strengths (see new anti-pattern).

## The Evidence Package

Written to `.orpheus/logs/build/{audit_id}/evidence-package.yaml` after every audit. Schema lives in `references/schemas/evidence-package-schema.md`. Shape:

```yaml
audit_id: a012
system: content-pipeline
audited_at: 2026-04-29T10:12:03.000Z
claim_matrix_source: .orpheus/claims.yaml   # or "default" if no override exists
overall_status: warnings                     # healthy | warnings | degraded | broken
health_score: 0.79

claims:
  - id: workflow_termination
    statement: "The job dependency graph is a DAG (terminates in bounded steps)"
    validation_method: proof
    status: proven                           # proven | checked | attested | unverified
    evidence:
      - type: dag_snapshot
        source: registry.yaml
        hash: sha256:3f2a...
        captured_at: 2026-04-29T10:12:01.000Z
    exceptions: []
    renewal_trigger: "dependency edge added, removed, or retargeted"
    next_review_required_on: "structural change to registry.yaml"
    owner: surgeon

  - id: tool_contract_soundness
    statement: "Every producer/consumer contract chain has matching required fields and compatible types"
    validation_method: policy-as-code
    status: checked
    evidence:
      - type: contract_chain_check
        checker: contract-compat-checker
        result_summary: "all chains compatible, 2 unused output fields (advisory)"
    exceptions:
      - id: unused_field_research_expert_sources
        severity: advisory
        description: "research-expert produces 'sources' but no downstream consumes it"
    renewal_trigger: "any contract.yaml modified"
    next_review_required_on: "contract change"
    owner: surgeon

renewal_triggers_active: []                  # populated when inputs changed since last audit
recommendations: [ ... ]                     # unchanged from pre-Stage-1
```

The three fields doing the real work:

- **status** is stronger than pass/fail. `proven` means the property is mathematically decidable and the decision came out positive; `checked` means policy-as-code passed; `attested` means evidence was present and well-formed; `unverified` is used when a claim's validation could not run (graceful degradation). A reviewer reading `checked` should not assume `proven`, and the Auditor is prohibited from labeling up.

- **evidence[].hash** and **captured_at** make the evidence auditable after the fact. A later Auditor run can detect "the artifact changed but this claim was not re-evaluated," which is the operationalization of renewable approval.

- **renewal_trigger** is natural language so a human or the Doctor/Surgeon can reason about it; `next_review_required_on` is the machine-checkable condition the Auditor compares against on its next invocation.

## How to Evaluate Whether This Adds Value

Stage 1 is a framing change, and framing changes are easy to hand-wave about. Here is a concrete evaluation method a reviewer (or CI) can run to falsify the claim that Stage 1 is useful. The rule of thumb: **Stage 1 adds value if and only if a reviewer can answer questions the pre-Stage-1 Auditor could not answer, without reading source files.**

### The Six-Question Test

After Stage 1 is deployed, pick any ORPHEUS system (the meta-system itself works as a test subject). Run the Auditor. Then attempt to answer each of the six "What Good Looks Like" questions from the whitepaper using **only the Auditor's output and the evidence package** — no reading of SKILL.md, no grepping, no memory of prior conversations.

| Question | Must be answerable from... | Passes Stage 1 if... |
|:---|:---|:---|
| 1. What critical properties have been proven, strongly verified, or continuously monitored? | `claims[].validation_method` + `status` | reviewer can list every `proof`/`policy-as-code` claim and its status |
| 2. What assumptions does the system rely on? | `claims[].statement` | reviewer can read each claim statement as an explicit assumption |
| 3. What tools can it call, with what scope, on whose authority? | `tool_contract_soundness` evidence + registry | reviewer sees which workers each expert may dispatch, from the evidence package only |
| 4. What sensitive data can influence decisions? | Out of scope for Stage 1 (needs `information_flow` claim — Stage 2+) | **expected to fail this one** — that is the point of staging |
| 5. What changed since the last approval decision? | `renewal_triggers_active` | reviewer can name every stale claim without inspecting files |
| 6. Which assurances remain valid, and which must be re-established? | `claims[].status` + `renewal_triggers_active` | reviewer can partition the claim set into still-valid vs. needs-re-validation |

Stage 1 **passes** if the reviewer can answer 1, 2, 3, 5, and 6 from the artifact alone, and explicitly identifies question 4 as something Stage 1 does not yet answer. Stage 1 **fails** if any of the first, second, fifth, or sixth questions still require file reading — that would mean the vocabulary change didn't actually surface the information.

### The Reproducibility Test

Run the Auditor against the same system twice without making any changes. Compare the two `evidence-package.yaml` files:

- `evidence[].hash` values for every claim must be identical across runs
- `renewal_triggers_active` must be `[]` on the second run if it was `[]` on the first
- `overall_status` and `health_score` must match exactly

If any of those drift without a corresponding file change, the evidence package is unreliable and the capability does not add the advertised value. This test is mechanical and can be added to CI as a post-commit check on the ORPHEUS meta-system itself.

### The Modification Detection Test

This is the test that validates renewal triggers actually work.

1. Run the Auditor. Record the evidence package as `run-A.yaml`.
2. Make a single, isolated change — edit one `SKILL.md` to add a line, or bump a version string in a contract.
3. Run the Auditor again. Record as `run-B.yaml`.

Stage 1 passes this test if:

- Exactly the claims whose `renewal_trigger` matches the change type appear in `run-B.yaml`'s `renewal_triggers_active`
- No unrelated claims are flagged
- The `evidence[].hash` of the affected claim differs between run-A and run-B, while unrelated claims' hashes are unchanged

This is the falsifiable version of "the renewal triggers actually connect claim to evidence." If a SKILL.md edit does not surface the affected claim, the mapping is wrong and needs fixing before Stage 2 depends on it.

### The Comparison Test

Take a pre-Stage-1 Auditor report (from git history, or regenerate by temporarily reverting) and a Stage-1 report on the same system. Ask a reviewer who has never seen the system which report they would prefer for a deployment decision. If the answer is not consistently the Stage-1 report, the framing change is not landing and the work should be reconsidered before Stage 2.

### What the Tests Do Not Prove

None of these tests prove that the *claims themselves* are well-chosen for your system. A default catalog is a starting point, not a complete safety case. The whitepaper is explicit: provable assurance is "an operating model in which each critical claim is linked to a validation method, evidence source, owner, and renewal trigger," and picking the critical claims is a human judgment that the Auditor cannot automate.

What Stage 1 does prove is that ORPHEUS can *carry* a claim matrix end-to-end: read it, evaluate it, emit evidence, detect staleness, report in the reviewer's vocabulary. The value of that infrastructure grows with the quality of the claims the system author writes, which is why Stage 2 (custom claims authored during Builder) matters.

## Relationship to Existing ORPHEUS Principles

Stage 1 does not conflict with any of the ten principles in `PRINCIPLES.md`. Alignment:

- **Principle 2 — The Coding Agent Is the Runtime.** The claim matrix is a YAML file; evaluation is the Auditor doing what it already does. Zero new runtime.
- **Principle 3 — Natural Language First.** Claim statements and renewal triggers are natural language. No DSL added.
- **Principle 6 — Decision Transparency.** The evidence package is the logical output of the decision-logging substrate — Stage 1 consumes what Principle 6 already produces.
- **Principle 7 — Self-Contained Portability.** The default claim catalog ships with the skill; the evidence package is written into `.orpheus/`. Generated systems remain portable.
- **Principle 8 — Error Chain Preservation.** `unverified` status with reason text preserves the failure chain when a validation method cannot run.

The tension worth naming: the whitepaper leans into formal methods. ORPHEUS is a natural-language framework. Stage 1 handles this by being honest about assurance strength — `proof` is reserved for actually-mathematical properties (DAG acyclicity), `policy-as-code` for mechanical checks, `evidence` for artifact inspection. This is the whitepaper's own recommendation ("Formal methods must be used selectively but deliberately") applied to the framework itself.

## References

- Schwartz, M. *Provable Assurance for Agentic Systems: A Verification Framework for Systems That Reason and Act.* 2026. [PDF](https://github.com/schwartz1375/ArtificialDiaries/blob/main/PDFs/provable_assurance_agentic_systems_whitepaper.pdf)
- ORPHEUS `PRINCIPLES.md` — the ten principles this capability is consistent with.
- ORPHEUS `references/schemas/claim-schema.md` — claim matrix schema.
- ORPHEUS `references/schemas/evidence-package-schema.md` — evidence package schema.
- ORPHEUS `references/claims/default-claims.yaml` — default claim catalog used when no `.orpheus/claims.yaml` is present.
