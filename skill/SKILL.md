---
name: orpheus
description: >
  ORPHEUS — Orchestrated Runtime Protocol for Hierarchical Execution Unified Skills.
  A meta-system for creating, running, and managing multi-skill orchestrated systems.
  Use this skill whenever the user wants to: create a new skill system, build a
  multi-skill pipeline, set up an orchestrated workflow, design an automated
  multi-step process, or RUN an existing ORPHEUS system (any project with a .orpheus/
  directory). Also use when the user says "create an ORPHEUS system", "build a skill
  system", "set up a pipeline", "run the pipeline", "execute the system", or describes
  any multi-step process they want automated with coordinated skills.
  Also activates for: modifying existing systems (add/remove skills), debugging
  pipeline failures, validating system health, and installing systems as standalone skills.
  Even if the user doesn't mention ORPHEUS by name, use this skill when they describe
  a multi-step automated workflow OR when .orpheus/ exists in the current directory
  and the user wants to execute, modify, debug, or validate that system.
---

# ORPHEUS — Multi-Skill Orchestration Framework

ORPHEUS replaces multi-agent systems with multi-skill systems. Instead of N separate agents with N separate LLM instances, ORPHEUS uses structured skill definitions that the coding agent executes through its native capabilities — tool access, subagent spawning, and filesystem I/O. No extra infrastructure needed.

## How It Works

1. **You describe** what you want (in natural language)
2. **ORPHEUS analyzes** your request and designs a skill hierarchy
3. **ORPHEUS generates** all skill files, contracts, and configuration
4. **The generated system** can execute immediately using the coding agent's native tools

A generated ORPHEUS system contains:
- **Orchestrator Skill**: decomposes requests into jobs, dispatches to experts
- **Expert Skills**: domain specialists that own specific job types, may delegate to workers
- **Worker Skills**: atomic task executors, reusable across experts
- **Contracts**: typed I/O schemas ensuring safe composition between skills
- **Logging**: structured decision trails for debugging and auditing

## Available Experts

| Expert | Status | Purpose | Definition |
|--------|--------|---------|------------|
| **Builder** | Active | Creates new ORPHEUS systems from NL descriptions | `references/experts/builder.md` |
| **Doctor** | Active | Diagnosis, debugging, and behavioral fixes | `references/experts/doctor.md` |
| **Auditor** | Active | Health checks, provable assurance claim matrix, evidence package generation | `references/experts/auditor.md` |
| **Surgeon** | Active | Structural modifications (add/remove/restructure skills) | `references/experts/surgeon.md` |

## Available Workers (used by experts)

| Worker | Purpose | Definition |
|--------|---------|------------|
| skill-md-generator | Generates/edits SKILL.md files | `references/workers/skill-md-generator.md` |
| contract-generator | Generates/edits contract.yaml files | `references/workers/contract-generator.md` |
| registry-updater | Creates/updates registry.yaml | `references/workers/registry-updater.md` |
| dag-validator | Validates dependency graphs | `references/workers/dag-validator.md` |
| contract-compat-checker | Checks contract compatibility | `references/workers/contract-compat-checker.md` |
| log-analyzer | Analyzes execution logs for patterns and issues | `references/workers/log-analyzer.md` |
| diff-generator | Produces human-readable change summaries | `references/workers/diff-generator.md` |

## Orchestration Protocol

### Phase 1: Detect Context

Check whether `.orpheus/` exists in the current working directory.

- **If .orpheus/ does NOT exist**: this is a new system request. Only the Builder can handle this. Proceed to Phase 2 with context = "no system".
- **If .orpheus/ exists**: this is an existing system. Read `.orpheus/system.yaml` to understand the system name and configuration. Proceed to Phase 2 with context = "existing system".

WHY: Without this check, you might attempt to create a system that already exists, or try to run/modify/debug a system that hasn't been created yet. Context detection prevents both.

### Phase 2: Classify Intent & Route

Determine what the user wants and route to the correct handler. Four experts are ACTIVE and FULLY IMPLEMENTED — you MUST use them, not improvise inline replacements.

**ACTIVE ROUTES — these experts exist and MUST be dispatched:**

| Intent | Signal Words | Route | How | Expert Definition |
|--------|-------------|-------|-----|-------------------|
| **Run/execute** | "run", "execute", "start", "launch", "against", "process" | **Runner** | Inline (Phase 3a) | Uses `.orpheus/orchestrator/SKILL.md` |
| **Create new** | "create", "build", "set up", "new", "design", "make" | **Builder** | Subagent (Phase 3b) | `references/experts/builder.md` |
| **Debug/fix** | "why", "failing", "broken", "fix", "debug", "wrong", "bad" | **Doctor** | Subagent (Phase 3d) | `references/experts/doctor.md` |
| **Validate/audit** | "validate", "check", "audit", "healthy", "verify", "scan" | **Auditor** | Subagent (Phase 3e) | `references/experts/auditor.md` |
| **Install** | "install", "standalone", "register" | **Installer** | Inline (Phase 3c) | Built into this SKILL.md |

**IMPORTANT:** When the user's intent matches Doctor or Auditor, you MUST dispatch them as subagents by reading their expert definition file and composing a dispatch prompt (see Phase 3d and 3e below). Do NOT attempt to perform diagnosis or auditing yourself inline. These experts have specialized protocols with worker dispatching that require their own subagent context.

| **Modify structure** | "add", "remove", "restructure", "split", "merge", "rename" | **Surgeon** | Subagent (Phase 3g) | `references/experts/surgeon.md` |

**Routing priority:** If `.orpheus/` exists and the intent doesn't clearly match any of the above, **default to Runner** — the most common operation on an existing system is executing it.

**If the request is ambiguous:** Ask the user to clarify before proceeding.

LOG this routing decision with reasoning: what signal words you detected, what alternatives you considered.

### Phase 3: Context Packaging (for all routes)

Before dispatching or executing, extract relevant context from the conversation. This is critical because subagents and even inline execution may lose conversation nuance if you don't package it explicitly.

**Scan the conversation history for:**
1. **Constraints:** "be careful", "skip X", "only do Y", "use conservative settings"
2. **Preferences:** "I want verbose output", "keep it brief", "focus on security"
3. **Prior context:** what the user said before the current request that informs intent
4. **Target/scope:** specific targets, URLs, file paths, parameters the user mentioned

**Package as a structured user_context block:**
```yaml
user_context:
  original_request: "{the user's exact current request}"
  constraints:
    - "{constraint extracted from conversation}"
  preferences:
    - "{preference extracted from conversation}"
  conversation_notes: "{relevant context from earlier messages}"
  target_scope: "{specific targets/parameters if mentioned}"
```

WHY: Without context packaging, subagents see only the dispatch prompt. An expert running a pentest won't know the user said "skip exploitation" three messages ago. This causes the "lost context" problem — the most dangerous failure mode because it produces incorrect results silently.

### Phase 3a: Route — Runner (Inline Execution)

**When:** `.orpheus/` exists AND intent is to run/execute the system.

The Runner executes **inline** — you (the meta-orchestrator) load the runtime orchestrator's protocol and execute it directly in your own context. This is NOT dispatched as a subagent.

WHY inline, not subagent: Running as a subagent would add an unnecessary nesting level (meta → runtime-orch → expert → worker = 4 levels). Inline execution keeps it at 3 levels (you-as-runtime-orch → expert → worker), preserves full conversation context, and eliminates the pass-through latency.

**Runner steps:**

1. **Read the runtime orchestrator's SKILL.md** from `.orpheus/orchestrator/SKILL.md`. This contains the system-specific orchestration protocol — routing rules, expert listings, concurrency config.

2. **Read the registry** from `.orpheus/registry.yaml` to understand available experts and workers.

3. **Generate an execution ID:**
   ```bash
   python3 .orpheus/scripts/generate-id.py e --base-path .orpheus
   ```

4. **Initialize execution directories:**
   ```bash
   bash .orpheus/scripts/init-execution.sh {eid} --base-path .orpheus
   ```

5. **Now follow the runtime orchestrator's 4-phase protocol** as described in its SKILL.md:
   - **Phase 1 — Decompose:** Break the user's request into jobs using the routing rules from the orchestrator SKILL.md. Include the user_context block in each job definition so experts see the full context.
   - **Phase 2 — Plan:** Compute parallel batches from the dependency graph.
   - **Phase 3 — Dispatch:** For each batch, dispatch experts as subagents (using the dispatch protocol from `references/protocols/dispatch-protocol.md`). Include the user_context block in every expert dispatch prompt. Dispatch all jobs in a batch as PARALLEL Agent calls.
   - **Phase 4 — Aggregate:** Read results, validate contracts, assemble logs, report to user.

6. **Assemble logs** after all jobs complete:
   ```bash
   python3 .orpheus/scripts/assemble-logs.py {eid} --base-path .orpheus
   ```

7. **Report results** to the user with: final output, job summary, any errors (using the full error chain if failures occurred).

### Phase 3b: Route — Builder (Subagent Dispatch)

**When:** `.orpheus/` does NOT exist AND intent is to create a new system.

1. **Read the Builder expert definition** from `references/experts/builder.md`.

2. **Compose the dispatch prompt:**

   ```
   You are the ORPHEUS Builder. You are operating within the ORPHEUS Meta-System.
   
   --- BEGIN EXPERT DEFINITION ---
   {paste the full contents of references/experts/builder.md}
   --- END EXPERT DEFINITION ---
   
   The ORPHEUS skill is installed at: {path to ~/.claude/skills/orpheus/}
   
   Available worker definitions (read on demand, do NOT read all upfront):
     - skill-md-generator: {orpheus_path}/references/workers/skill-md-generator.md
     - contract-generator: {orpheus_path}/references/workers/contract-generator.md
     - registry-updater: {orpheus_path}/references/workers/registry-updater.md
     - dag-validator: {orpheus_path}/references/workers/dag-validator.md
     - contract-compat-checker: {orpheus_path}/references/workers/contract-compat-checker.md
   
   Templates directory: {orpheus_path}/templates/
   Scripts directory: {orpheus_path}/scripts/
   Protocol references: {orpheus_path}/references/protocols/
   Schema references: {orpheus_path}/references/schemas/
   
   User request: {user_context.original_request}
   User constraints: {user_context.constraints}
   Working directory: {current working directory}
   
   Execute your protocol. Report results back when complete.
   ```

3. **Dispatch the Builder** using the Agent tool.

4. **Wait for completion.** Then present the created system to the user: directory tree, execution flow, skill count, validation status.

### Phase 3c: Route — Installer (Inline)

**When:** `.orpheus/` exists AND intent is to install as standalone skill.

1. Read `.orpheus/system.yaml` to get the system name
2. Read `.orpheus/orchestrator/SKILL.md` to get the orchestrator definition
3. Create a symlink (or wrapper SKILL.md) at `~/.claude/skills/{system_name}/SKILL.md` that:
   - Contains the orchestrator's frontmatter (name, description, type)
   - Points execution back to the project's `.orpheus/` directory
4. Inform the user: "{system_name} is now installed as a standalone Claude Code skill. It will trigger by name from any directory. Note: execution still reads/writes to {project_path}/.orpheus/."

WHY a wrapper, not a raw symlink: A symlinked SKILL.md would have relative paths that break when invoked from another directory. The wrapper SKILL.md uses absolute paths to the project's `.orpheus/` directory.

### Phase 3d: Route — Doctor (Subagent Dispatch)

**When:** `.orpheus/` exists AND intent is to debug, diagnose, or fix.

1. **Read the Doctor expert definition** from `references/experts/doctor.md`.

2. **Compose the dispatch prompt:**

   ```
   You are the ORPHEUS Doctor. You are operating within the ORPHEUS Meta-System.
   
   --- BEGIN EXPERT DEFINITION ---
   {paste the full contents of references/experts/doctor.md}
   --- END EXPERT DEFINITION ---
   
   The ORPHEUS skill is installed at: {path to ~/.claude/skills/orpheus/}
   System path: {current working directory}/.orpheus/
   
   Available worker definitions (read on demand):
     - log-analyzer: {orpheus_path}/references/workers/log-analyzer.md
     - diff-generator: {orpheus_path}/references/workers/diff-generator.md
     - skill-md-generator: {orpheus_path}/references/workers/skill-md-generator.md
     - contract-compat-checker: {orpheus_path}/references/workers/contract-compat-checker.md
   
   User complaint: {user_context.original_request}
   User context: {user_context block}
   Execution ID to analyze: {if specified, otherwise "most recent"}
   Target skill: {if specified, otherwise "not specified"}
   
   Execute your diagnosis protocol. Report findings back when complete.
   ```

3. **Dispatch the Doctor** using the Agent tool. Wait for completion.

4. **Check the Doctor's output.** If it contains an `escalation` block (structural issue needing Surgeon), inform the user and note it for future Surgeon dispatch.

### Phase 3e: Route — Auditor (Subagent Dispatch)

**When:** `.orpheus/` exists AND intent is to validate, audit, or check health.

1. **Read the Auditor expert definition** from `references/experts/auditor.md`.

2. **Compose the dispatch prompt:**

   ```
   You are the ORPHEUS Auditor. You are operating within the ORPHEUS Meta-System.
   
   --- BEGIN EXPERT DEFINITION ---
   {paste the full contents of references/experts/auditor.md}
   --- END EXPERT DEFINITION ---
   
   The ORPHEUS skill is installed at: {path to ~/.claude/skills/orpheus/}
   System path: {current working directory}/.orpheus/
   
   Available worker definitions (read on demand):
     - dag-validator: {orpheus_path}/references/workers/dag-validator.md
     - contract-compat-checker: {orpheus_path}/references/workers/contract-compat-checker.md
     - registry-updater: {orpheus_path}/references/workers/registry-updater.md
     - log-analyzer: {orpheus_path}/references/workers/log-analyzer.md
   
   Audit scope: {determine from user request: "full" if general, or specific scope}
   User context: {user_context block}
   
   Execute your audit protocol. Report the health report when complete.
   ```

3. **Dispatch the Auditor** using the Agent tool. Wait for completion.

4. **Present the health report** to the user. If the Auditor recommends fixes, inform the user which expert can handle each (Doctor or Surgeon).

### Phase 3g: Route — Surgeon (Subagent Dispatch)

**When:** `.orpheus/` exists AND intent is to add, remove, restructure, split, merge, or rename skills.

1. **Read the Surgeon expert definition** from `references/experts/surgeon.md`.

2. **Compose the dispatch prompt:**

   ```
   You are the ORPHEUS Surgeon. You are operating within the ORPHEUS Meta-System.
   
   --- BEGIN EXPERT DEFINITION ---
   {paste the full contents of references/experts/surgeon.md}
   --- END EXPERT DEFINITION ---
   
   The ORPHEUS skill is installed at: {path to ~/.claude/skills/orpheus/}
   System path: {current working directory}/.orpheus/
   
   Available worker definitions (read on demand):
     - skill-md-generator: {orpheus_path}/references/workers/skill-md-generator.md
     - contract-generator: {orpheus_path}/references/workers/contract-generator.md
     - registry-updater: {orpheus_path}/references/workers/registry-updater.md
     - dag-validator: {orpheus_path}/references/workers/dag-validator.md
     - contract-compat-checker: {orpheus_path}/references/workers/contract-compat-checker.md
     - diff-generator: {orpheus_path}/references/workers/diff-generator.md
   
   User request: {user_context.original_request}
   User context: {user_context block}
   Operation: {classified operation type from user request}
   Target: {skill/job being operated on}
   
   Execute your protocol. Present the change plan for user approval before applying changes.
   ```

3. **Dispatch the Surgeon** using the Agent tool. Wait for completion.

4. **Present the Surgeon's report:** changes made, validation results, diff summary.

### Phase 4: Receive Results & Report

**For Runner:** Results are already available inline — you executed the protocol yourself. Present the final output with job summary and any errors (using full error chains).

**For Builder:** Read the expert's output. Check:
- Does `.orpheus/` now exist with the expected structure?
- Read the build log if available
- Check validation results
- Present: directory tree, execution flow, skill count

**For Installer:** Confirm the installation path and note the project binding.

**For errors at any level:** Present the full error chain (see dispatch protocol's Error Chain Format). Never flatten errors to just "execution failed" — always show the root cause.

## Compound Operations (Future)

When multiple experts are needed for a single request:

- **"Debug and fix"**: Doctor diagnoses → Doctor fixes (if behavioral) or Surgeon fixes (if structural)
- **"Add and validate"**: Surgeon adds → Auditor validates
- **"Audit and heal"**: Auditor finds issues → Doctor/Surgeon fixes → Auditor re-validates

These require dispatching experts sequentially, where the next expert receives the prior expert's output. The meta-orchestrator manages this chain.

## Anti-Patterns

- **Don't try to create a system if .orpheus/ already exists.** The user probably wants to run or modify the existing system. Ask first.
- **Don't spawn a subagent for "run" requests.** Use inline execution. Subagent dispatch for running wastes a nesting level, loses conversation context, and adds latency. The Runner route exists specifically to avoid this.
- **Don't improvise when an expert exists.** Builder, Doctor, and Auditor are FULLY IMPLEMENTED with specialized protocols and worker dispatching. When the user's intent matches one of these experts, you MUST dispatch it by reading its definition from `references/experts/` and composing a subagent prompt — NEVER attempt to perform their job inline yourself. Your inline improvisation will be worse than the expert's dedicated protocol.
- **All experts are active — never tell the user something is "coming soon" or "not available."** Builder, Doctor, Auditor, and Surgeon are ALL fully implemented. Check the routing table — every row has an active route. If you find yourself saying "not yet available," you are wrong.
- **Don't skip context packaging.** Every dispatch — whether to Builder subagent or inline expert — must include the structured user_context block. Without it, skills miss critical user constraints.
- **Don't flatten errors.** When presenting failures, always show the full error chain from root cause to symptom. "Job failed" is never an acceptable error message.
- **Don't send all worker definitions in the dispatch prompt.** The expert reads worker definitions on demand. Sending everything upfront wastes context.
- **Don't forget scripts are local.** Generated systems have their own scripts at `.orpheus/scripts/`. Always use local paths when running a system, not the global ORPHEUS install path.

## Logging Protocol

For meta-orchestrator operations, write log entries as `entry-NNN.yaml` to `.orpheus/logs/build/{operation_id}/` (for Builder/Surgeon/Doctor/Auditor operations) or to `.orpheus/logs/runtime/{eid}/orchestrator/` (for Runner operations):

1. Log when you start: what the user requested, the full user_context block
2. Log your routing decision: which route and why
3. Log dispatch or inline execution start
4. Log each major phase transition during inline execution
5. Log completion: what was produced, any errors (full chain)
6. Log any retries with the failure context that was added

Reference `references/protocols/logging-protocol.md` for the full log entry schema.

## Design Reference

The complete ORPHEUS architecture is documented in the project's `DESIGN.md`. Key sections:
- Section 5: Execution Model (how dispatching works)
- Section 6: Concurrency Model (parallel execution)
- Section 8: Observability & Logging (structured logging)
- Section 17: ORPHEUS Meta-System (this meta-system's architecture)

## Provable Assurance

The Auditor evaluates each system against an explicit assurance claim matrix and emits an evidence package suitable for renewable approval decisions. See:

- `references/PROVABLE_ASSURANCE.md` — framing and motivation
- `references/protocols/assurance-protocol.md` — operational protocol (matrix loading, claim evaluation, renewal triggers, evidence emission)
- `references/schemas/claim-schema.md` — claim format and catalog `extends` semantics
- `references/schemas/evidence-package-schema.md` — output artifact schema
- `references/claims/default-claims.yaml` — default claim catalog (7 structural claims)
- `references/claims/preview-claims.yaml` — opt-in preview catalog (forward-looking unverified claims)

The Builder generates a stub `.orpheus/claims.yaml` for new systems. System authors add custom claims by editing that file. Surgeon and Doctor mention which claims their actions affect, recommending the user run the Auditor afterward.
