# skill-md-generator

A worker that generates or edits SKILL.md files for ORPHEUS skill systems.

## Purpose

This worker creates properly structured SKILL.md files from specifications. It reads templates, fills in domain-specific content, and ensures every generated skill has the required sections (frontmatter, protocol, quality gate, logging, anti-patterns). This is the most impactful worker in the system — the quality of generated SKILL.md files determines whether the entire skill system works.

## Contract

**Input:**
- `operation`: "create" or "edit"
- `skill_type`: "orchestrator", "expert", or "worker"
- `specification`: Object containing the domain-specific content:
  - For orchestrator: system_name, system_description, expert_table, routing_rules, concurrency_config, worker_summary
  - For expert: expert_name, expert_description, system_name, role_description, execution_protocol, worker_table, quality_gate, contract_summary
  - For worker: worker_name, worker_description, system_name, purpose, task_protocol, output_format, constraints, model_preference, tools
- `target_path`: Where to write the generated SKILL.md
- `existing_content`: (edit only) Current SKILL.md content to modify

**Output:**
- `file_path`: Path where the SKILL.md was written
- `line_count`: Number of lines in the generated file
- `sections_included`: List of sections present in the generated file

## Task Protocol

### For "create" operations:

1. **Read the appropriate template** based on `skill_type`:
   - orchestrator → read `templates/orchestrator-skill.md.tmpl` (path relative to the ORPHEUS skill directory)
   - expert → read `templates/expert-skill.md.tmpl`
   - worker → read `templates/worker-skill.md.tmpl`

2. **Fill in the template placeholders** using values from `specification`:
   - Replace each `{{PLACEHOLDER}}` with the corresponding value
   - For multi-line values (execution_protocol, task_protocol), preserve proper markdown indentation
   - For table values (expert_table, worker_table, routing_rules), format as markdown tables

3. **Ensure critical sections are present.** Every generated SKILL.md MUST have:
   - For orchestrator: Orchestration Protocol (4 phases), Routing Rules, Error Recovery, Logging Protocol, Anti-Patterns
   - For expert: Execution Protocol (multi-phase), Quality Gate, Error Handling, Logging Protocol, Anti-Patterns
   - For worker: Task Protocol (numbered steps), Output Format, Constraints, Logging Protocol

4. **Inject the logging protocol section** if not already in the template output. Every skill needs logging instructions — see `references/protocols/logging-protocol.md` for the standardized content.

5. **Write the completed SKILL.md** to `target_path`.

6. **Verify the output:**
   - Count lines (warn if orchestrator > 250 lines, expert > 400 lines, worker > 150 lines — these are targets, not hard limits)
   - Confirm all required sections are present
   - Confirm frontmatter has: name, description, type, version, orpheus.system

### For "edit" operations:

1. Read `existing_content` to understand the current structure
2. Identify which section(s) need modification based on `specification`
3. Apply targeted edits — preserve sections not mentioned in the specification
4. Write the modified SKILL.md to `target_path`

## Output Format

Write your result YAML to the result_path provided:

```yaml
job_id: "{job_id}"
status: completed
skill_name: skill-md-generator
output:
  file_path: "{target_path}"
  line_count: {number}
  sections_included:
    - "frontmatter"
    - "execution protocol"
    - "quality gate"
    - "logging protocol"
    - "anti-patterns"
```

## Constraints

- NEVER generate a SKILL.md without a logging protocol section — the Doctor depends on skills logging their decisions
- NEVER hardcode model preferences unless the specification explicitly requests it — use "inherit" as default
- NEVER skip the frontmatter — it's required for Claude Code to recognize the skill
- Keep the `description` field in frontmatter "pushy" — include specific trigger phrases so the skill activates reliably
- Explain WHY in instructions, not just WHAT — skills with reasoning produce more reliable LLM behavior
