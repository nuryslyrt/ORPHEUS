# ORPHEUS Logging Protocol

This document defines how every ORPHEUS skill writes structured log entries during execution. Consistent logging enables the Doctor to diagnose issues, the Auditor to validate health, and users to understand system behavior.

## How Logging Works

Each log entry is a **separate YAML file** written to your `log_path` directory (provided in your dispatch context). This per-entry-file design avoids concurrent write conflicts when parallel workers log to the same job directory.

## File Naming

| Skill Type | Pattern | Example |
|------------|---------|---------|
| Orchestrator | `entry-{NNN}.yaml` | `entry-001.yaml`, `entry-002.yaml` |
| Expert | `entry-{NNN}.yaml` | `entry-001.yaml`, `entry-002.yaml` |
| Worker | `entry-{worker-name}-{NNN}.yaml` | `entry-web-search-worker-001.yaml` |

Workers prefix with their name because they share a log directory with their parent expert. This prevents filename collisions.

Increment the counter sequentially within your execution. Start at 001.

## Mandatory Events

Every skill MUST log these events. Skipping any of them makes the system opaque to diagnosis and auditing.

### 1. skill.invoked (when you start executing)
```yaml
id: "log-{eid}-001"
timestamp: "{ISO 8601 with ms}"
execution_id: "{eid}"
source:
  skill_name: "{your skill name}"
  skill_type: "{orchestrator|expert|worker}"
  job_id: "{job_id or null}"
  parent_skill: "{who dispatched you, or null}"
level: info
category: lifecycle
event: "skill.invoked"
summary: "{your skill name} started on {brief task description}"
```

### 2. Every decision you make (category: decision)
```yaml
id: "log-{eid}-{NNN}"
timestamp: "{ISO 8601 with ms}"
execution_id: "{eid}"
source:
  skill_name: "{your skill name}"
  skill_type: "{your type}"
  job_id: "{job_id or null}"
  parent_skill: "{parent or null}"
level: info
category: decision
event: "{decision event name, e.g., expert.complexity_assessment}"
summary: "{one line summarizing the decision}"
decision:
  question: "{what you were deciding}"
  options_considered:
    - "{option A}"
    - "{option B}"
  chosen: "{which option you picked}"
  reasoning: "{1-3 sentences explaining WHY you chose this. This is the most important field — it enables the Doctor to understand your logic.}"
  confidence: 0.85
```

**Why decisions MUST include reasoning:** Without reasoning, the Doctor can only see WHAT happened. With reasoning, the Doctor can determine WHETHER the decision was correct. A wrong decision with good reasoning suggests a data problem. A wrong decision with bad reasoning suggests a skill instruction problem.

### 3. Every delegation (dispatching workers or jobs)
```yaml
level: info
category: delegation
event: "worker.dispatched"
summary: "Dispatched {worker_name} for {task description}"
detail:
  worker_name: "{name}"
  task_summary: "{brief description}"
  batch_id: "{shared ID for parallel dispatches}"
```

### 4. Every error encountered
```yaml
level: error  # or warn for non-fatal
category: error
event: "{error event, e.g., worker.failed}"
summary: "{what went wrong}"
detail:
  error_type: "{classification}"
  error_message: "{details}"
  recovery_action: "{what you did about it}"
```

### 5. skill.completed (when you finish)
```yaml
level: info
category: lifecycle
event: "skill.completed"
summary: "{your skill name} completed {brief result description}"
detail:
  duration_ms: {execution time}
  output_summary: "{what you produced}"
```

## Decision Events by Skill Type

| Skill Type | Decisions to Log |
|------------|-----------------|
| Orchestrator | Intent decomposition, dispatch strategy (parallel vs sequential), expert assignment, error recovery |
| Expert | Complexity assessment (solo vs delegate), worker selection, quality gate evaluation |
| Worker | Minimal — workers follow checklists, but log any judgment calls |

## Anti-Patterns

| Anti-Pattern | Why It Fails | Do This Instead |
|---|---|---|
| Logging without reasoning | Doctor can't determine if decision was correct | Always include reasoning in decision entries |
| Skipping skill.invoked/completed | Cannot compute execution duration or trace flow | Always log lifecycle bookends |
| Using level=info for errors | Errors log won't catch it | Use warn/error/fatal appropriately |
| Giant detail objects | Bloats logs, slows assembly | Keep detail concise — summaries, not full data |
| Not logging worker dispatches | Can't trace delegation chain | Log every dispatch with worker name and task |
