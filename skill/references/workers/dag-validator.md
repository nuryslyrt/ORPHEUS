# dag-validator

A worker that validates the dependency graph of an ORPHEUS skill system.

## Purpose

ORPHEUS systems define jobs with dependencies between them. These dependencies form a Directed Acyclic Graph (DAG). This worker checks that the graph is valid: no cycles (which would cause infinite loops), no orphaned jobs (defined but never referenced), no dangling references (dependencies pointing to non-existent jobs), and the graph can be topologically sorted into executable batches.

## Contract

**Input:**
- `system_path`: Path to the .orpheus/ directory root
- `proposed_changes`: (optional) Hypothetical changes to validate before applying — object with added_jobs[], removed_jobs[], modified_dependencies{}

**Output:**
- `is_valid`: boolean — whether the graph passes all checks
- `issues`: array of {type, severity, description} objects
- `graph_summary`: {total_jobs, total_dependencies, max_depth, parallel_batches[], longest_path[]}

## Task Protocol

1. **Discover jobs.** Read all files in `.orpheus/state/execution/{eid}/jobs/` (for runtime validation) OR read the registry and orchestrator SKILL.md to infer the job structure (for build-time validation).

2. **If proposed_changes provided**, apply them hypothetically — add/remove/modify jobs in memory without touching files.

3. **Build the adjacency list.** For each job:
   - Node: job_id
   - Edges: job_id → each dependency in dependencies[]

4. **Check for cycles** using depth-first search:
   - Mark nodes as: unvisited, in-progress, completed
   - If you encounter an in-progress node during DFS, a cycle exists
   - Report the cycle path (e.g., "A → B → C → A")

5. **Check for dangling references:**
   - For each dependency reference, verify the target job_id exists
   - Report any references to non-existent jobs

6. **Check for orphaned jobs:**
   - A job is orphaned if no other job depends on it AND it is not in the first batch (no dependencies itself has)
   - Note: jobs with no dependencies are NOT orphaned — they are roots. Jobs that nothing depends on are terminal nodes (also fine). Orphaned means unreachable from the normal flow.

7. **Compute topological ordering** (batch assignment):
   - Batch 1: all jobs with no dependencies
   - Batch N: all jobs whose dependencies are all in batches < N
   - If any job cannot be assigned (all its dependencies are not in earlier batches), there may be an undetected issue

8. **Compute summary statistics:**
   - total_jobs: count of all jobs
   - total_dependencies: count of all dependency edges
   - max_depth: number of batches
   - parallel_batches: list of [batch_number, [job_ids]]
   - longest_path: the longest chain of sequential dependencies

## Output Format

```yaml
job_id: "{job_id}"
status: completed
skill_name: dag-validator
output:
  is_valid: true
  issues: []
  graph_summary:
    total_jobs: 4
    total_dependencies: 3
    max_depth: 3
    parallel_batches:
      - batch: 1
        jobs: [research, analyze]
      - batch: 2
        jobs: [write-report]
      - batch: 3
        jobs: [format-output]
    longest_path: [research, write-report, format-output]
```

When issues are found:
```yaml
output:
  is_valid: false
  issues:
    - type: cycle
      severity: critical
      description: "Cycle detected: write-report → review → write-report"
    - type: dangling_reference
      severity: error
      description: "Job 'format-output' depends on 'edit-report' which does not exist"
```

## Constraints

- This worker is READ-ONLY — it never modifies job files or any other state
- Report ALL issues found, not just the first one — the user needs the complete picture
- A valid DAG has: no cycles, no dangling references, and all jobs assignable to batches
- Issue severity levels: `critical` (cycles — system cannot execute), `error` (dangling refs — jobs will fail), `warn` (orphaned jobs — not harmful but wasteful)
