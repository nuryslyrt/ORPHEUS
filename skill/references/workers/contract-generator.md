# contract-generator

A worker that generates or edits contract.yaml files for ORPHEUS skills.

## Purpose

This worker creates typed input/output schemas that enable safe composition between skills. Contracts define what a skill accepts and produces, allowing the system to validate that skill chains are compatible before execution.

## Contract

**Input:**
- `operation`: "create" or "edit"
- `skill_name`: Name of the skill this contract belongs to
- `specification`: Object containing:
  - `input_required`: Map of field_name → {type, description}
  - `input_optional`: Map of field_name → {type, description, default}
  - `output_required`: Map of field_name → {type, description}
  - `output_optional`: Map of field_name → {type, description}
- `target_path`: Where to write the contract.yaml
- `existing_content`: (edit only) Current contract.yaml content

**Output:**
- `file_path`: Path where the contract.yaml was written
- `field_count`: Total number of fields defined

## Task Protocol

1. **Read the contract template** from `templates/contract.yaml.tmpl`

2. **For each field in the specification**, generate proper YAML:
   ```yaml
   field_name:
     type: string
     description: "What this field contains"
   ```
   For optional fields with defaults, add:
   ```yaml
   field_name:
     type: number
     description: "What this field contains"
     default: 5
   ```
   For enum fields, add:
   ```yaml
   field_name:
     type: enum
     description: "What this field contains"
     enum_values: [value1, value2, value3]
   ```

3. **Fill the template placeholders:**
   - `{{SKILL_NAME}}` → skill_name
   - `{{VERSION}}` → "1.0.0"
   - `{{INPUT_REQUIRED}}` → generated YAML for required input fields
   - `{{INPUT_OPTIONAL}}` → generated YAML for optional input fields
   - `{{OUTPUT_REQUIRED}}` → generated YAML for required output fields
   - `{{OUTPUT_OPTIONAL}}` → generated YAML for optional output fields

4. **If a section has no fields** (e.g., no optional inputs), write an empty marker: `{}` or omit the section.

5. **Write the completed contract.yaml** to `target_path`.

## Output Format

```yaml
job_id: "{job_id}"
status: completed
skill_name: contract-generator
output:
  file_path: "{target_path}"
  field_count: {total fields across all sections}
```

## Constraints

- Every field MUST have both `type` and `description` — fields without descriptions are useless for compatibility checking
- `type` must be one of: string, number, boolean, object, array, enum
- `enum_values` is required when type=enum, and must have at least 2 values
- Use consistent naming: field names should be snake_case
- The contract `name` field MUST match the skill's name in its SKILL.md frontmatter
