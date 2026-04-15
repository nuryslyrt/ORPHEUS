# Contract Schema

A Skill Contract defines the input/output interface of a skill, enabling safe composition between skills in a pipeline.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Same as the skill name this contract belongs to |
| `version` | string | Yes | Semantic version of the contract (e.g., "1.0.0") |
| `input` | object | No | Input specification (see sub-fields below) |
| `output` | object | No | Output specification (see sub-fields below) |

### input / output Sub-Structure

Both `input` and `output` have the same sub-structure:

| Field | Type | Description |
|-------|------|-------------|
| `required` | object | Map of field_name → field definition. All must be present. |
| `optional` | object | Map of field_name → field definition. May be absent. |

### Field Definition

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `string` \| `number` \| `boolean` \| `object` \| `array` \| `enum` |
| `description` | string | What this field contains and how it is used |
| `enum_values` | string[] | Only for type=enum. List of valid values. |
| `default` | any | Only for optional fields. Default value if not provided. |

## Example

```yaml
name: web-search-worker
version: "1.0.0"

input:
  required:
    query:
      type: string
      description: "Search query to execute"
  optional:
    max_results:
      type: number
      description: "Maximum number of results to return"
      default: 5
    source_filters:
      type: array
      description: "Domain allowlist for filtering results"
    recency:
      type: string
      description: "Time filter (e.g., 'last 7 days', 'last month')"

output:
  required:
    results:
      type: array
      description: "Array of {url, title, summary} objects"
    query_used:
      type: string
      description: "Actual query that was executed (may differ from input)"
  optional:
    total_found:
      type: number
      description: "Total results available (not just returned)"
```

## Validation Rules

1. `name` must be non-empty and match the skill's name in frontmatter
2. `version` must follow semantic versioning (major.minor.patch)
3. Every field definition must have `type` and `description`
4. `type` must be one of the 6 valid type values
5. `enum_values` is required when type=enum, forbidden otherwise
6. `default` should only appear under `optional` fields

## Compatibility Rules

When checking if Skill A's output is compatible with Skill B's input:

1. Every field in B's `input.required` must exist in A's `output.required` or `output.optional`
2. Types must match (string=string, array=array, etc.)
3. Extra fields in A's output that B doesn't consume are acceptable (no error)
4. Missing optional fields in A's output are acceptable if B has defaults
