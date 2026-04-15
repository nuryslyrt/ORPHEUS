# ORPHEUS Runtime Orchestration Protocol

This is the core protocol that every runtime orchestrator (in generated systems) follows. It defines the 4-phase cycle: Decompose → Plan → Dispatch → Aggregate.

When the orchestrator-skill.md.tmpl generates a runtime orchestrator, it references this protocol for the detailed execution logic.

## Phase 1: Intent Decomposition

Break the user's request into discrete jobs.

### Steps

1. **Read the user request.** Understand what the user wants as a final output.

2. **Identify discrete work units.** A job is a unit of work that:
   - Has a clear input and output
   - Can be assigned to a single expert
   - Has a well-defined completion criteria
   - Is independently testable

3. **For each job, determine:**
   - `job_id`: kebab-case identifier (e.g., `research-quantum`)
   - `title`: human-readable description
   - `assigned_expert`: which expert handles it (use routing rules)
   - `input`: what data the expert needs
   - `expected_output`: what the orchestrator expects back
   - `dependencies`: which other jobs must complete first

4. **Write job definitions** to `.orpheus/state/execution/{eid}/jobs/{job-id}.yaml` following the job schema (see references/schemas/job-schema.md).

5. **LOG decision:** How you decomposed the request. Include options you considered (e.g., "3 sequential jobs vs 2 parallel + 1 sequential") and why you chose your approach.

### Decision Guidance

- If the request maps to a SINGLE clear task → create 1 job (Direct mode)
- If the request has multiple distinct phases → create N jobs with dependencies
- If phases are independent of each other → they can run in parallel
- If phase B needs output from phase A → B depends on A
- When in doubt, prefer more granular jobs — they enable parallelism and better error isolation

## Phase 2: Execution Planning

Compute parallel batches from the dependency graph.

### Steps

1. **Build the dependency DAG.** Read all job files. For each job, note its dependencies.

2. **Compute batches using topological ordering:**
   ```
   Batch 1 = all jobs with NO dependencies (or empty dependency list)
   Batch 2 = all jobs whose dependencies are ALL in Batch 1
   Batch 3 = all jobs whose dependencies are ALL in Batch 1 or 2
   ... continue until all jobs are assigned to a batch
   ```

3. **Write the execution manifest** to `.orpheus/state/execution/{eid}/manifest.yaml`:
   ```yaml
   execution_id: "{eid}"
   system: "{system_name}"
   status: running
   started_at: "{ISO 8601}"
   user_request: "{original request}"
   plan:
     batches:
       - batch: 1
         jobs: [job-a, job-b]
         status: pending
       - batch: 2
         jobs: [job-c]
         status: pending
   ```

4. **LOG decision:** Your batching strategy — which jobs are parallel, which are sequential, and why.

### Single-Job Optimization

If there is only 1 job AND it is simple enough (no workers needed, estimated < 30 seconds):
- Skip subagent dispatch overhead
- Execute the expert's protocol **inline** (in your own context)
- Read the expert's SKILL.md, follow its protocol directly
- This is called "inline execution" — it saves a subagent spawn for trivial tasks

## Phase 3: Dispatch

Execute batches sequentially. Within each batch, dispatch all jobs in parallel.

### Steps

For each batch in order:

1. **For each job in the batch**, compose a dispatch prompt following the dispatch protocol (see references/protocols/dispatch-protocol.md):
   - Read the assigned expert's SKILL.md content
   - Include the full execution context (paths, available workers)
   - If the job has dependency_results, include those paths

2. **Dispatch ALL jobs in the batch using PARALLEL Agent tool calls.** Include all Agent() calls in a single message — this makes them execute concurrently.

3. **Wait for all subagents in the batch to complete.**

4. **For each completed job:**
   - Read the result from `.orpheus/state/execution/{eid}/results/{job-id}.yaml`
   - Check if the result exists and contains the expected_output fields
   - Update the job's status in its job file: `status: completed`
   - Update the batch status in the manifest

5. **Handle failures:**
   - If a job failed and `retry_count < max_retries`:
     - Increment retry_count in the job file
     - Re-dispatch the job (alone, not with the full batch)
     - LOG decision: why retrying (transient error? timeout?)
   - If retries exhausted, check the `escalation` strategy in system.yaml:
     - `user`: stop and ask the user what to do
     - `skip`: mark job as failed, continue with remaining batches (dependent jobs will also be skipped)
     - `fallback`: try a different expert if one is available

6. **Proceed to the next batch** only when the current batch is fully resolved (all jobs completed or handled).

### Dispatch Checklist

Before dispatching, verify:
- [ ] init-execution.sh has been run (execution directories exist)
- [ ] All job YAML files are written
- [ ] Manifest is written with batch plan
- [ ] Expert SKILL.md files are readable at the paths in the registry
- [ ] For dependent jobs: all dependency results exist

## Phase 4: Aggregation

Collect results and assemble the final output.

### Steps

1. **Read all job results** from `.orpheus/state/execution/{eid}/results/`.

2. **Validate results against contracts:**
   - For each job, check that the result contains all `expected_output.fields`
   - LOG any contract violations as warnings (missing fields, unexpected format)

3. **Combine results into the final output** for the user:
   - The combination strategy depends on the system's purpose
   - Sequential pipelines: the last job's result IS the final output
   - Parallel pipelines: merge results from all jobs
   - The orchestrator SKILL.md should define how to combine for this specific system

4. **Assemble logs** by running the assemble script:
   ```bash
   python3 {orpheus_skill_path}/scripts/assemble-logs.py {eid} --base-path .orpheus
   ```
   This produces timeline.log.yaml, decisions.log.yaml, errors.log.yaml, and execution.log.yaml.

5. **Update the manifest** with final status: `status: completed` (or `failed` if any critical jobs failed).

6. **Report to the user:**
   - Present the final output
   - Summarize: how many jobs ran, how many succeeded/failed, total duration
   - If there were errors or warnings, mention them briefly
   - Reference the log path for detailed inspection

## Error Recovery Summary

| Situation | Action |
|-----------|--------|
| Job failed, retries available | Re-dispatch with incremented retry_count |
| Job failed, retries exhausted, strategy=user | Stop, ask user |
| Job failed, retries exhausted, strategy=skip | Skip job + all dependents |
| Job failed, retries exhausted, strategy=fallback | Try different expert |
| Contract violation (missing fields) | Log warning, continue if non-critical |
| Subagent timeout | Treat as job failure, apply retry logic |
| All jobs in batch failed | Stop execution, report to user |

## Anti-Patterns

| Anti-Pattern | Why It Fails | Do Instead |
|---|---|---|
| Dispatching dependent jobs in parallel | Job B reads empty results because Job A isn't done | Respect batch ordering — dependencies MUST be in earlier batches |
| Inline execution for complex jobs | Context window pressure, no isolation | Use subagents for anything needing workers or deep reasoning |
| Skipping log assembly | Doctor and Auditor can't function | Always run assemble-logs.py in Phase 4 |
| Retrying without adjusting context | Same failure repeats | Add context about the failure to the retry dispatch prompt |
| Not updating manifest | Recovery from crashes impossible | Update manifest at every state transition |
