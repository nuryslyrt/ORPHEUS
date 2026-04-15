# diff-generator

A worker that produces human-readable summaries of changes made to an ORPHEUS system.

## Purpose

When the Doctor applies a behavioral fix or the Surgeon restructures a system, the user needs to understand exactly what changed and why. This worker takes a list of file changes and produces a clear, structured diff summary. It turns raw file modifications into an understandable narrative.

## Contract

**Input:**
- `changes`: Array of change objects, each containing:
  - `file_path`: Path to the changed file
  - `operation`: "created" | "modified" | "deleted"
  - `before_snippet`: (modified/deleted only) The relevant content before the change
  - `after_snippet`: (created/modified only) The relevant content after the change
  - `reason`: Why this change was made (1-2 sentences)

**Output:**
- `summary`: Human-readable markdown summary of all changes
- `files_created`: Array of created file paths
- `files_modified`: Array of modified file paths
- `files_deleted`: Array of deleted file paths
- `structural_impact`: "none" | "minor" | "major"

## Task Protocol

1. **Classify the overall impact:**
   - `none`: No structural changes (only content edits within existing sections)
   - `minor`: New files added or small structural changes (added a worker, edited a contract)
   - `major`: Core structure changed (dependency graph modified, experts added/removed, orchestrator routing changed)

2. **For each change, generate a diff block:**

   For **created** files:
   ```
   + CREATED: {file_path}
     Reason: {reason}
     Content: {first 10 lines or key sections of after_snippet}
   ```

   For **modified** files:
   ```
   ~ MODIFIED: {file_path}
     Reason: {reason}
     Before: {before_snippet, trimmed to relevant section}
     After:  {after_snippet, trimmed to relevant section}
   ```

   For **deleted** files:
   ```
   - DELETED: {file_path}
     Reason: {reason}
     Was: {brief description of what the file contained}
   ```

3. **Generate a summary narrative** (3-5 sentences):
   - What was the overall goal of these changes?
   - How many files were affected?
   - What is the structural impact?
   - Are there any follow-up actions needed?

4. **Write the complete summary** to result_path.

## Output Format

```yaml
job_id: "{job_id}"
status: completed
skill_name: diff-generator
output:
  summary: |
    ## Changes Summary
    
    **Goal:** Fixed overly verbose output from the summarizer expert.
    **Impact:** Minor (1 file modified, no structural changes)
    
    ### Modified Files
    
    ~ **experts/summarizer-expert/SKILL.md**
      Reason: Tightened output length constraints in the execution protocol
      ```diff
      - Produce a comprehensive summary covering all aspects of the topic
      + Produce a concise summary (max 500 words) focusing on key findings only
      ```
    
    ### Follow-up
    - Re-run the pipeline to verify the fix produces shorter output
    - No contract changes needed (output format unchanged)
  files_created: []
  files_modified:
    - "experts/summarizer-expert/SKILL.md"
  files_deleted: []
  structural_impact: "none"
```

## Constraints

- Keep diff snippets focused — show only the changed section, not the entire file
- Always include the `reason` for each change — diffs without context are confusing
- The summary should be understandable by someone who hasn't seen the raw files
- If `before_snippet` is very long (>20 lines), trim to the most relevant portion and note "[trimmed]"
- For structural_impact assessment: changing contracts, dependencies, or routing = "major". Adding/removing workers = "minor". Editing instructions within an existing SKILL.md = "none".
