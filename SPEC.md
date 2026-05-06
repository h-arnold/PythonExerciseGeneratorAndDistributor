# README Exercise Links Specification

## Status

- Draft v1.1
- Updated to align with repository planning templates and lock agreed README rendering decisions.

## Purpose

This document defines the intended behaviour for README exercise-list rendering in generated template repositories.

The feature will be used to:

- present each selected exercise as a markdown link to the exported student notebook
- use metadata-backed exercise titles as readable link text
- organise mixed-construct selections into clear construct-based sections

This feature is not intended to:

- change exercise selection rules in the template CLI
- alter canonical packaging paths or runtime variant behaviour

## Agreed product decisions

1. Exercise ordering is fixed to sorted exercise keys.
2. README entries are grouped by construct heading, with heading text derived from metadata `construct` and displayed as proper title-case words.
3. Each exercise link appears as a numbered item under its construct heading.
4. Link text is taken from metadata `title` in canonical `exercise.json`.
5. Link targets are canonical exported student notebook paths: `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`.
6. Metadata/render failures are wrapped and raised as a packager-specific `ValueError` with exercise-key context.

## Existing system constraints

Documented constraints that shape the design are below.

### Backend or API constraints already in place

- README generation is owned by `TemplatePackager.generate_readme(...)` in `scripts/template_repo_cli/core/packager.py`.
- Packaging orchestration in `scripts/template_repo_cli/cli.py` passes selected exercise keys to packager methods.

### Current data-shape constraints

- Canonical metadata is in `exercises/<construct>/<exercise_key>/exercise.json`.
- Canonical metadata includes `title`, `construct`, and exercise identity fields.
- README template replacement contract currently uses `{TEMPLATE_NAME}` and `{EXERCISE_LIST}` placeholders.

### Consumer or integration architecture constraints

- Packaged repository layout must preserve canonical student notebook paths.
- Existing packager tests in `tests/template_repo_cli/test_packager.py` assert README generation and package validity, so behaviour changes must be covered there.

## Domain and contract recommendations

### Why this approach is preferable

- It improves student and teacher readability by replacing opaque exercise keys with human titles.
- It keeps output deterministic and testable via stable ordering rules.
- It scales to multi-construct exports without requiring separate templates per construct.

### Recommended data shapes

#### Selected exercise render input

```json
{
  "exercise_key": "ex002_sequence_modify_basics",
  "construct": "sequence",
  "title": "Sequence Modify Basics",
  "student_notebook_path": "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
}
```

#### README section model

```json
{
  "display_construct": "Sequence",
  "entries": [
    {
      "index": 1,
      "title": "Sequence Modify Basics",
      "href": "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
    }
  ]
}
```

### Naming recommendation

Prefer:

- `exercise_key`
- `construct`
- `title`
- `student_notebook_path`

Avoid:

- `exercise_id` for README ordering logic
- `slug` as README link text

This naming avoids ambiguity between display labels and canonical identity keys.

### Validation recommendation

#### Consumer

- Selection inputs remain exercise-key based.
- Empty selection behaviour remains unchanged unless already constrained elsewhere.

#### Backend

- Fail fast when required metadata for a selected exercise cannot be loaded.
- Reject blank or missing metadata title for README rendering.
- Raise packager-specific `ValueError` and include exercise-key context and chained cause.

### Display-resolution recommendation

- Construct display labels are resolved from metadata `construct` by replacing underscores with spaces and applying title case.
- README grouping is determined by construct while preserving sorted exercise-key ordering of entries.

## Feature architecture

### Placement

- Canonical implementation surface is the template packager README generation path.
- Parallel README rendering logic elsewhere is explicitly out of scope.

### Proposed high-level tree

```text
TemplatePackager
└── README Rendering
    ├── Metadata resolution per selected exercise key
    ├── Construct grouping and display formatting
    └── Numbered markdown link composition
```

### Out of scope for this surface

- Altering template selection UX or CLI flags.
- Changing notebook packaging location or adding solution notebook links.

## Data loading and orchestration

### Required datasets or dependencies

- canonical exercise metadata (`exercise.json`) for each selected exercise key
- selected exercise keys passed from template CLI to packager

### Prefetch or initialisation policy

#### Startup

- No startup prefetch changes required for this feature.

#### Feature entry

- Metadata is loaded during README generation for the selected exercise set.

#### Manual refresh

- No manual refresh control is part of this feature.

### Query or transport additions

- No transport, API, or query-layer additions required.

## Core view model or behavioural model

### Suggested shape

```json
{
  "construct_sections": [
    {
      "display_construct": "Sequence",
      "entries": [
        {
          "exercise_key": "ex002_sequence_modify_basics",
          "title": "Sequence Modify Basics",
          "href": "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
        }
      ]
    }
  ]
}
```

### Derivation or merge rules

#### Entry derivation

- Sort selected exercise keys lexicographically.
- For each key, load metadata and derive notebook link path from canonical construct and key.

#### Group derivation

- Group entries by metadata construct key.
- Render one heading per construct with numbered entries below.

### Sort order or priority rules

1. Primary ordering is sorted exercise keys.
2. Group ordering follows first appearance by sorted exercise-key iteration.
3. Numbering restarts per construct section and follows entry order in that section.

## Main user-facing surface specification

### Recommended components or primitives

- Markdown heading per construct section.
- Numbered markdown list entries for notebook links.

### Fields, columns, or visible sections

1. Template title at top of README via `{TEMPLATE_NAME}`.
2. Construct heading per group.
3. Numbered link entries using exercise title text.

### Sorting, filtering, or navigation rules

- Sorting is deterministic and based on sorted exercise keys.
- No README-side filtering or search is introduced.
- Existing template placeholders remain unchanged.

### Rendering rules

#### Construct section with one or more exercises

- Show heading in proper title-case words.
- Show numbered links under the heading.

#### Metadata failure for a selected exercise

- Abort README generation and raise packager-specific `ValueError`.
- Include exercise-key context and preserve root exception via chaining.
- Expected error message format example:
  - `README generation failed for exercise 'ex002_sequence_modify_basics': missing or invalid title metadata`

## Workflow specification

## Generate README during packaging

### Eligible inputs or preconditions

- Selected exercise keys are provided by existing CLI selection flow.
- Canonical exercise metadata files exist for selected exercises.

### Inputs, fields, or confirmation copy

- `template_name`
- `exercises` (selected exercise keys)

### Behaviour

- Load README template content from `template_repo_files/README.md.template` (or fallback content if absent).
- Build construct-grouped numbered markdown links using metadata title and canonical student notebook paths.
- Replace `{TEMPLATE_NAME}` and `{EXERCISE_LIST}` placeholders and write `README.md`.
- Raise packager-specific `ValueError` on metadata/render failures.

## Error, loading, and empty-state rules

### Blocking failure

- Missing or invalid metadata required for a selected exercise is blocking.
- User must receive a packager-specific `ValueError` with exercise-key context.
- Error text should follow the documented message-format style to support deterministic test assertions.

### Partial-load or partial-success failure

- Partial success is not allowed for README rendering; generation fails fast.

### Empty states

#### No selected exercises

- Existing behaviour is preserved unless constrained by upstream selection validation.

## Accessibility and usability notes

- Human-readable titles improve scanability compared with raw exercise keys.
- Construct headings reduce ambiguity when multiple constructs are packaged together.
- Numbered lists provide predictable order cues.

## Backend changes required to support agreed behaviour

1. Update packager README rendering contract.
   - Build metadata-backed grouped markdown output.
   - Keep sorted exercise-key ordering semantics.
2. Add packager-specific error wrapping.
   - Wrap metadata and rendering failures in `ValueError`.
   - Include exercise-key context and chained cause.
3. Update README template wording only if needed for grouped output clarity.
   - Preserve `{TEMPLATE_NAME}` and `{EXERCISE_LIST}` placeholders.

## Planning handoff notes

- Implementation must preserve existing packaging and selection contracts.
- Test-first delivery should update packager tests before or alongside logic changes.
- Do not introduce exercise-id-based ordering in v1.

## Testing expectations

- Unit coverage for packager README generation includes:
  - construct heading rendering
  - numbered link formatting
  - title-based link text
  - canonical notebook link targets
  - sorted exercise-key ordering
  - packager-specific `ValueError` wrapping on metadata failures
- Existing package integrity checks remain green.

## Documentation and rollout notes

- Update packager docstrings/comments only where behaviour contract changes.
- No migration or rollout toggle is required.
- Deferred enhancement ideas (for example, optional ordering modes) remain out of v1.

## V1 scope recommendation

### Include in v1

- Metadata title-based markdown notebook links.
- Construct-grouped headings with numbered entries.
- Packager-specific `ValueError` wrapping for metadata/render failures.

### Defer from v1

- Alternative ordering modes.
- Additional README grouping levels beyond construct.
- Optional inclusion of solution notebook links.
