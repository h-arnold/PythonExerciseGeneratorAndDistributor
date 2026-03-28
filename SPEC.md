# SPEC: Canonical Student-Only Template Repository Layout (Option A)

## 1. Purpose

Define the target packaging behaviour for `template_repo_cli` so exported Classroom template repositories:

- preserve the canonical exercise tree shape under `exercises/<construct>/<exercise_key>/`,
- include only student-facing exercise assets,
- keep exercise-local tests beside each exercise,
- remain compatible with repository test discovery and notebook self-check execution.

This specification adopts **Option A**: **no per-exercise metadata files** in packaged templates.

---

## 2. Scope

### In scope

- Exported template repository file layout produced by `template_repo_cli`.
- Notebook path resolution contract for packaged repositories.
- Test discovery and runtime compatibility in packaged repositories.
- Packaging validation rules for allowed/forbidden exported assets.

### Out of scope

- Changes to source-repository canonical authoring layout.
- Changes to exercise content itself.
- Teacher workflow for extending templates post-packaging.
- Inclusion of solution notebooks in template exports.

---

## 3. Target packaged structure

For every selected exercise key `exNNN_<construct>_<slug>`:

```text
exercises/
  <construct>/
    <exercise_key>/
      notebooks/
        student.ipynb
      tests/
        test_<exercise_key>.py
        ... (exercise-local support files required by the test)
```

Top-level shared test/runtime infrastructure required by autograding and self-check execution remains included at repository root (for example `tests/`, `exercise_runtime_support/`, workflow files, and other packaging base files).

---

## 4. Required inclusions

A valid packaged template must include:

1. Student notebook per selected exercise at:
   - `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
2. Exercise-local tests per selected exercise at:
   - `exercises/<construct>/<exercise_key>/tests/`
3. Shared runtime/test infrastructure needed for:
   - pytest execution,
   - autograde payload support,
   - notebook self-check support via `run_notebook_checks('<exercise_key>')`.

---

## 5. Explicit exclusions (Option A)

Packaged template repositories must **not** include:

- `exercise.json` (or any per-exercise metadata file),
- `exercises/<construct>/<exercise_key>/notebooks/solution.ipynb` (or any solution notebook surface),
- teacher-facing authoring documentation copied from exercise folders (unless separately specified),
- template-repo maintenance/authoring-only tooling not needed by students.

---

## 6. Behavioural requirements

### 6.1 Exercise key identity

- Exercise identity remains the canonical `exercise_key` string.
- Notebook self-check cells continue to call:
  - `run_notebook_checks('<exercise_key>')`
- Self-check execution must resolve to the packaged student notebook in the canonical exercise-local path.

### 6.2 Packaged resolver behaviour

In packaged repositories (metadata-free export mode):

- resolving by `exercise_key` must target:
  - `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- path-like string inputs continue to fail fast where current contracts require key-only inputs.

### 6.3 pytest discovery compatibility

- Packaged repositories must preserve test discovery over configured roots (`tests`, `exercises`).
- Selected exercise tests under `exercises/.../tests/` must collect and run successfully.

---

## 7. Validation rules

Packaging validation must enforce all of the following:

1. Each selected exercise has exactly one exported student notebook at canonical exercise-local path.
2. Each selected exercise exports its exercise-local `tests/` tree.
3. No solution notebooks are exported.
4. No per-exercise metadata files are exported.
5. Shared runtime/test infrastructure required by autograding and self-checks is present.

Validation should fail fast with clear messages when any rule is violated.

---

## 8. Compatibility and migration expectations

- This change intentionally replaces flattened student notebook export paths for packaged templates.
- Existing template repos generated with flattened notebook paths are legacy packaging outputs.
- Updated packaging tests must codify the new canonical student-only export shape.

---

## 9. Acceptance criteria

A packaging run is accepted only if:

1. For each selected exercise:
   - `exercises/<construct>/<exercise_key>/notebooks/student.ipynb` exists,
   - `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py` exists.
2. No `exercise.json` exists in exported output.
3. No solution notebook exists in exported output.
4. `pytest --collect-only -q` in packaged output collects exercise tests under `exercises/.../tests/`.
5. `run_notebook_checks('<exercise_key>')` works from the packaged notebook environment for selected exercises.

---

## 10. Non-goals confirmed with requester

- No requirement to support teacher extension of packaged templates.
- No requirement to preserve authoring metadata in exported templates.
- No requirement to include solution variants in exported templates.
