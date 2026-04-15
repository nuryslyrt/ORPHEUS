# contract-compat-checker

A worker that checks contract compatibility across the skill chain in an ORPHEUS system.

## Purpose

In an ORPHEUS pipeline, Expert A's output feeds into Expert B's input (via job dependencies). This worker verifies that every such handoff is safe — that A's output contract provides all the fields B's input contract requires, with compatible types. Without this check, skills can pass data that downstream skills can't use, causing silent failures or garbage output.

## Contract

**Input:**
- `system_path`: Path to the .orpheus/ directory root
- `scope`: "full" (check all chains) or "pair" (check one specific connection)
- `source_skill`: (pair scope only) Name of the upstream skill
- `target_skill`: (pair scope only) Name of the downstream skill

**Output:**
- `compatible`: boolean — whether all checked chains are compatible
- `issues`: array of {source, target, field, issue_type, description} objects
- `field_mapping`: object showing how source outputs map to target inputs

## Task Protocol

### For scope = "full":

1. **Read the registry** to get all skill entries and their contract paths

2. **Read the orchestrator SKILL.md** to understand routing rules and the implied job flow. Alternatively, read the system.yaml routing configuration.

3. **Determine the flow chain.** For each job dependency (Job B depends on Job A):
   - Expert-A (assigned to Job A) produces output per its contract
   - Expert-B (assigned to Job B) expects input per its contract
   - Check: does Expert-A's output satisfy Expert-B's input?

4. **For each connection in the chain**, perform the compatibility check (see "Compatibility Check" below).

5. **Also check expert-to-worker compatibility** within each expert:
   - The expert must be able to provide what workers expect as input
   - Worker outputs must provide what the expert needs to synthesize its result

6. **Report all issues found** across all connections.

### For scope = "pair":

1. Read the contract.yaml for `source_skill` and `target_skill`
2. Perform the compatibility check between source.output and target.input
3. Report issues

### Compatibility Check Algorithm

For a connection where Skill A's output feeds Skill B's input:

```
For each field in B.input.required:
  - Does this field exist in A.output.required OR A.output.optional?
    - NO → ISSUE: "Missing required field '{field}' in {A}'s output"
    - YES → Check type compatibility:
      - Same type? → OK
      - Different type? → ISSUE: "Type mismatch for '{field}': {A} outputs {type_a}, {B} expects {type_b}"

For each field in B.input.optional:
  - If it exists in A.output with a different type → ISSUE (type mismatch)
  - If it doesn't exist in A.output → OK (optional fields may be absent)

For each field in A.output.required that B.input doesn't reference:
  - This is a WARNING, not an error: "Unused field '{field}' in {A}'s output — {B} does not consume it"
```

## Output Format

```yaml
job_id: "{job_id}"
status: completed
skill_name: contract-compat-checker
output:
  compatible: true
  issues: []
  field_mapping:
    research-expert -> writing-expert:
      findings: "findings → research_content (compatible: string → string)"
      sources: "sources → source_list (compatible: array → array)"
      confidence: "confidence → (not consumed, warning)"
```

When issues are found:
```yaml
output:
  compatible: false
  issues:
    - source: research-expert
      target: writing-expert
      field: methodology
      issue_type: missing_required
      description: "writing-expert requires 'methodology' but research-expert's output does not include it"
    - source: writing-expert
      target: review-expert
      field: word_count
      issue_type: type_mismatch
      description: "writing-expert outputs word_count as string, review-expert expects number"
```

## Constraints

- This worker is READ-ONLY — it never modifies contracts or any other files
- Report ALL incompatibilities, not just the first — the Builder/Surgeon needs the full picture to decide what to fix
- Unused output fields are WARNINGS, not errors — over-producing is safe, under-producing is not
- Type compatibility is strict: string != number, array != object. The only exception: "object" is compatible with any structured type (object, array) as a loose match.
