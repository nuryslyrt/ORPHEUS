# ORPHEUS Core Principles

These are the foundational principles that define ORPHEUS and distinguish it from every other orchestration framework. They are not aspirational goals — they are architectural commitments baked into every file, every protocol, and every decision in the system.

---

## Principle 1: Skills, Not Agents — Right Tool for the Right Problem

**Multi-agent systems are powerful. But for most orchestration use cases, they are more tool than the problem requires.**

When you need to hang a picture, you reach for a nail and a tap hammer. You don't bring in a pneumatic framing nailer, an air compressor, and a generator. The pneumatic nailer is a better tool for framing a house — but for hanging a picture, it's overhead that adds complexity without adding value.

The same principle applies to LLM orchestration. Multi-agent systems — with separate LLM instances, inter-agent protocols, message queues, and independent state management per agent — are the right tool for complex scenarios: long-running autonomous systems, multi-model pipelines across different providers, or systems requiring hard process isolation. ORPHEUS does not claim to replace these.

But most orchestration tasks in practice are simpler than that. Most "agents" in production are really just *a system prompt + a tool subset + a routing rule.* They don't need their own LLM instance. They don't need inter-process communication. They don't need independent deployment. They need a clear role definition and a way to be invoked when needed.

For these cases — and they are the majority — ORPHEUS offers a lighter primitive: **skills.** A skill is a structured natural language definition that tells the coding agent what role to assume, what inputs to expect, what outputs to produce, and when to delegate. A skill is a file, not a process. It lives on disk, not in a container.

The coding agent already provides:
- LLM reasoning (the brain)
- Tool access (file I/O, code execution, web search, shell)
- Context management (conversation state, file reading)
- Subagent spawning (parallel execution)

These are the same capabilities that individual agents in a multi-agent system provide for themselves. When the problem doesn't require the full agent abstraction, that duplication is waste. ORPHEUS eliminates it by matching the tool to the problem.

**When to use ORPHEUS (the tap hammer):**
- Orchestrated workflows with clear stages and handoffs
- Systems where a single coding agent can provide all needed capabilities
- Teams that want NL-first configuration over code-first frameworks
- Projects where zero-infrastructure deployment matters

**When to use multi-agent systems (the pneumatic nailer):**
- Long-running autonomous agents with persistent independent state
- Pipelines that mix different LLM providers (Claude + GPT + local models)
- Systems requiring hard process isolation for fault tolerance
- Scenarios where agents must operate across different machines or networks

The right tool for the right problem. ORPHEUS exists because the skill-shaped tool was missing from the toolbox.

**What this means in practice:**
- One coding agent, not N agent instances — when the problem fits
- Skills are loaded as instructions, not deployed as services
- No inter-agent communication protocols — skills share a filesystem
- Adding a new capability means writing a markdown file, not deploying a service
- Multi-agent frameworks remain the right choice when the problem genuinely requires them

---

## Principle 2: The Coding Agent Is the Runtime

**ORPHEUS adds zero runtime infrastructure. The coding agent provides everything.**

Every other orchestration framework introduces infrastructure: Python packages, API servers, message queues, state databases, Docker containers, or at minimum, executable code that must be installed and maintained. ORPHEUS introduces none of these.

The coding agent (Claude Code) natively provides:
- **Tool execution:** file I/O, shell commands, web search, code execution
- **Subagent spawning:** the Agent tool dispatches parallel workers with fresh contexts
- **State persistence:** the filesystem IS the state store
- **Skill loading:** SKILL.md files are the native extension mechanism

ORPHEUS simply structures how these native capabilities are used. It is a protocol, not a platform. The entire framework is 31 markdown and script files totaling ~4,000 lines. No compilation. No package manager. No dependency resolution. Copy a folder, and it works.

**What this means in practice:**
- Installation is `cp -r skill/ ~/.claude/skills/orpheus/`
- No `pip install`, no `npm install`, no `docker pull`
- No API keys beyond what the coding agent already uses
- No version conflicts, no dependency hell, no breaking updates
- Works offline (minus web-dependent skills)

---

## Principle 3: Natural Language First

**If you can describe it, you can build it. If you can name the problem, you can fix it.**

ORPHEUS operates entirely through natural language at every level:

- **System creation:** "Build me a system that researches, writes, and publishes articles"
- **System execution:** "Run the pipeline against quantum computing"
- **Diagnosis:** "Why did the research step fail?"
- **Modification:** "Add a fact-checking expert between research and writing"
- **Validation:** "Audit my system and tell me if it's healthy"

Skill definitions themselves are natural language. An expert's execution protocol is written as numbered phases with reasoning, not as Python classes or YAML state machines. A worker's task protocol is a checklist, not an API contract.

This is not a simplification or a toy abstraction. It's a recognition that LLMs follow structured natural language instructions more reliably than they follow formal specifications — especially when those instructions include the *reasoning behind each step*.

**What this means in practice:**
- Non-developers can create orchestrated systems
- Modifying system behavior means editing a markdown file
- The system is self-documenting — the skill definitions ARE the documentation
- No code translation layer between intent and implementation

---

## Principle 4: Self-Building Meta-System

**ORPHEUS is itself an ORPHEUS system. The framework builds, diagnoses, validates, and evolves itself using its own patterns.**

The ORPHEUS Meta-System consists of:
- An **Orchestrator** that routes user intent to the correct expert
- A **Builder** expert that creates new skill systems
- A **Doctor** expert that diagnoses failures and applies behavioral fixes
- An **Auditor** expert that runs health checks and produces validation reports
- A **Surgeon** expert that performs structural modifications with cascading analysis
- **7 shared workers** that experts compose differently for their tasks

This is not a design pattern imposed on users while the framework itself uses a different architecture. ORPHEUS practices what it preaches. The meta-system is structured exactly like the systems it creates: orchestrator → experts → workers, with contracts, logging, and state management.

This self-referential property serves as a validation proof: if ORPHEUS can describe and manage itself, it is expressive enough to describe and manage any orchestrated system.

**What this means in practice:**
- The framework validates its own thesis by existing
- Users see the pattern demonstrated before they use it
- The meta-system can audit, diagnose, and modify itself
- Every feature of the framework is exercised by the framework's own operation

---

## Principle 5: Full-Lifecycle Management

**Create, run, diagnose, validate, and structurally modify — all through the same interface, all in natural language.**

Most frameworks address creation and execution. ORPHEUS addresses the complete lifecycle:

| Phase | What Happens | Who Handles It |
|-------|-------------|----------------|
| **Create** | Describe what you want → system is generated | Builder |
| **Run** | Execute the system against real inputs | Runner (inline) |
| **Diagnose** | Something went wrong → find and fix root cause | Doctor |
| **Validate** | Proactive health check before things go wrong | Auditor |
| **Modify** | Add, remove, or restructure skills | Surgeon |
| **Re-validate** | Confirm modifications didn't break anything | Auditor |

These phases compose into cycles:
- **Audit → Heal → Re-Audit:** Find issues, fix them, verify fixes
- **Diagnose → Fix → Verify:** Identify root cause, apply fix, confirm resolution
- **Modify → Validate → Run:** Change structure, check health, execute

The user never leaves the natural language interface. The same prompt format that creates a system also modifies it, debugs it, and validates it.

**What this means in practice:**
- No separate CLI tools for different lifecycle phases
- No context switching between "development" and "operations" modes
- The system evolves through conversation, not code commits
- Every lifecycle action is logged with full decision reasoning

---

## Principle 6: Decision Transparency

**Every decision is logged with what was decided, what alternatives were considered, and WHY.**

Most systems log what happened: "Agent X called Tool Y at time T." This tells you the *sequence of events* but not the *reasoning behind them*. When something goes wrong, you can see the symptom but not the cause.

ORPHEUS logs decisions at a deeper level:

```yaml
decision:
  question: "How should the user request be decomposed into jobs?"
  options_considered:
    - "Single job: handle everything with one expert"
    - "3 jobs: research → write → format (sequential)"
    - "4 jobs: research + analyze (parallel) → write → format"
  chosen: "3 jobs: research → write → format (sequential)"
  reasoning: "Request has 3 distinct phases with linear dependencies.
    Research must complete before writing, writing before formatting.
    No parallelizable independent work identified."
  confidence: 0.92
```

This isn't optional metadata. It's a mandatory part of every skill's execution protocol. The Doctor uses decision logs to diagnose issues — not just "what failed" but "what reasoning led to the failure." An incorrect decision with good reasoning points to bad input data. An incorrect decision with bad reasoning points to bad skill instructions. The distinction changes the fix entirely.

**What this means in practice:**
- Post-mortems are data-driven, not speculative
- The Doctor can trace any failure to the decision that caused it
- Decision patterns across executions reveal systematic issues
- Users can audit the system's reasoning, not just its outputs
- Confidence scores flag uncertain decisions for human review

---

## Principle 7: Self-Contained Portability

**Generated systems carry everything they need. No framework dependency at runtime.**

When ORPHEUS builds a system, the resulting `.orpheus/` directory contains:
- All skill definitions (orchestrator, experts, workers)
- All contracts (typed I/O schemas)
- All runtime scripts (ID generation, log assembly, validation, directory initialization)
- System configuration and skill registry

The generated system does not reference the global ORPHEUS installation at runtime. You could delete `~/.claude/skills/orpheus/` and the generated system would still execute through the coding agent's native skill mechanism.

This is a deliberate architectural choice. Systems that depend on their framework for execution are fragile — framework updates can break deployed systems, different users may have different framework versions, and the framework becomes a single point of failure.

ORPHEUS systems are like compiled binaries: the compiler (Builder) is needed to create them, but not to run them.

**What this means in practice:**
- Generated systems survive ORPHEUS uninstallation
- Systems can be shared between users by copying the `.orpheus/` directory
- No version coupling between framework and generated systems
- Multiple systems at different "versions" coexist without conflict
- CI/CD pipelines can run systems without installing ORPHEUS

---

## Principle 8: Error Chain Preservation

**Errors are never flattened. The full chain from root cause to symptom is preserved at every level.**

In a 3-level system (orchestrator → expert → worker), an error at the worker level must travel through two layers before reaching the user. At each layer, context is typically lost:

```
Worker: "WebSearch returned 0 results for 'CVE Apache 2.4.41'"
Expert: "CVE lookup failed"
Orchestrator: "Job failed"
User sees: "Execution failed" ← useless
```

ORPHEUS requires every level to wrap — not replace — the error from below:

```
error:
  level: orchestrator
  message: "Job 'vuln-analysis' failed after 2 retries"
  recovery_attempted: "Retried with same expert"
  original_error:
    level: expert
    message: "CVE lookup failed — worker returned empty results"
    recovery_attempted: "Dispatched alternative worker"
    original_error:
      level: worker
      message: "WebSearch returned 0 results for 'CVE Apache 2.4.41'"
      recovery_attempted: "Retried with broader query"
```

The user sees the full chain. The Doctor sees the full chain. Recovery attempts at every level are documented. Root cause identification is immediate, not archaeological.

**What this means in practice:**
- Users never see "execution failed" without root cause detail
- The Doctor can identify the exact point of failure without guessing
- Recovery attempts at each level are documented (no duplicate effort)
- Error patterns across executions are detectable (same root cause recurring)

---

## Principle 9: Composition Over Configuration

**Complex systems are built by composing simple skills, not by configuring monolithic frameworks.**

ORPHEUS has no configuration DSL, no YAML state machines, no graph definition language, and no Python class hierarchies. Complex behavior emerges from composing simple primitives:

- An **orchestrator** that routes and dispatches
- **Experts** that own domains and delegate
- **Workers** that execute atomic tasks
- **Contracts** that define interfaces between them

A content pipeline and a penetration testing system use the same primitives in different arrangements. The difference is in the skill definitions (natural language), not in framework configuration.

Workers are reusable across experts. The same `web-search-worker` serves a research expert, a fact-checking expert, and a vulnerability analysis expert. The worker doesn't know or care which expert dispatched it — it follows its protocol and writes its result.

**What this means in practice:**
- Learning one pattern (orchestrator → expert → worker) covers all use cases
- Workers built for one system are reusable in others
- System complexity grows by adding skills, not by adding configuration
- No framework-specific DSL to learn — just markdown with structure

---

## Principle 10: Inline Execution for Runtime

**When running a generated system, the meta-orchestrator executes the runtime protocol directly — no unnecessary subagent layer.**

This is an architectural principle born from identifying a real problem. A naive implementation would dispatch the generated system's orchestrator as a subagent, creating 4 nesting levels:

```
Meta-orchestrator [L1] → Runtime orchestrator [L2] → Expert [L3] → Worker [L4]
```

Level 1 does almost nothing — it reads a file and forwards a request. It wastes a context window, adds latency, and consumes a nesting level. Worse, it loses the user's conversation context because subagents don't inherit conversation history.

ORPHEUS uses **inline execution** for the Runner route: the meta-orchestrator loads the runtime orchestrator's SKILL.md and executes its protocol directly in its own context. This produces 3 levels:

```
Meta-as-runtime [L1] → Expert [L2] → Worker [L3]
```

The meta-orchestrator has full access to the conversation, so user constraints ("skip exploitation," "be conservative") are naturally preserved. No context packaging can fully replace having the actual conversation available.

**What this means in practice:**
- 3 nesting levels, not 4 — matches the design's intended depth
- Full conversation context preserved during execution
- No pass-through latency from an idle intermediate subagent
- User constraints and preferences don't require special handling for the run path

---

## How the Principles Relate

```
                    Skills, Not Agents (#1)
                           │
                    defines the core abstraction
                           │
              ┌─────────────┴──────────────┐
              │                            │
    Coding Agent Is                 Natural Language
     the Runtime (#2)                  First (#3)
              │                            │
        no infrastructure             no code required
              │                            │
              └─────────────┬──────────────┘
                            │
                    Self-Building
                   Meta-System (#4)
                            │
                   proves the pattern works
                            │
              ┌─────────────┼──────────────┐
              │             │              │
     Full-Lifecycle    Decision      Error Chain
    Management (#5)  Transparency   Preservation (#8)
              │         (#6)              │
         create/run/     │          never lose
         fix/validate    │          root cause
              │       log the WHY         │
              └─────────────┼──────────────┘
                            │
              ┌─────────────┼──────────────┐
              │             │              │
     Self-Contained   Composition      Inline
    Portability (#7)  Over Config (#9) Execution (#10)
              │             │              │
       no framework    simple parts    3 levels,
       dependency     compose into     not 4
       at runtime     complex systems
```

These principles are not independent features. They form a coherent philosophy: **the multi-agent paradigm introduces accidental complexity that a skill-based approach eliminates, while preserving — and in some cases improving — the capabilities that multi-agent systems provide.**
