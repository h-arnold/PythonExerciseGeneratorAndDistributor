# WORKFLOW_SPEC: template_repo_cli canonical-only flow

## Purpose
Keep `scripts/template_repo_cli/` aligned with the repository's post-cutover canonical model.

## Canonical flow
1. **Selection**
   - Select exercises by metadata-backed `exercise_key`, construct, type, or exercise-key pattern.
   - Do not retain legacy directory scanning or any other legacy-layout compatibility branch.

2. **Collection**
   - Resolve the student notebook from the canonical exercise directory.
   - Read canonical exercise tests from `exercises/<construct>/<exercise_key>/tests/`.
   - Export notebooks and tests to exercise-local paths only.
   - If a previous helper only existed to support legacy layout or test scaffolding, delete it or relocate it under `tests/`.

3. **Packaging**
   - Copy the whole canonical exercise test directory into the packaged workspace.
   - Do not special-case root-level `tests/` as an exercise export target.

4. **GitHub auth handling**
   - Use one shared classifier for permission/auth failures.
   - Reuse that classifier both for retry decisions and for user-facing guidance.

5. **Error handling**
   - Catch expected operational failures close to the CLI boundary.
   - Let unexpected internal defects surface so they can be fixed rather than masked.

## Invariants
- Exercise identity remains the canonical `exercise_key`.
- Variant behaviour remains controlled by `--variant` and `PYTUTOR_ACTIVE_VARIANT`.
- Exported templates remain metadata-free and student-facing.
- No legacy-layout compatibility remains in the steady-state template CLI path.
