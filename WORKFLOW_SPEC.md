# WORKFLOW_SPEC — Classroom 50 Bundle Deployment

This document records the operational path for deploying the teacher-side
bundle. `SPEC.md` defines the contract; this document defines the layout and
the steps a teacher performs.

The grading manifest, fresh-install dependency target, pytest trust boundary,
pinned upstream snapshot, and assignment-schema matrix described in earlier
revisions of this file are withdrawn. The code committed against them has been
reverted.

## Source layout

The source repository remains canonical:

```text
exercises/<construct>/<exercise_key>/
├── exercise.json
├── notebooks/
│   ├── student.ipynb
│   └── solution.ipynb
└── tests/
    ├── test_<exercise_key>.py
    ├── expectations.py
    └── student_checker_support.py
```

The builder takes a JSON exercise set of `{construct, exercise_key}` records,
the current `exercise_runtime_support/` source, and an output directory.

## Build output

```text
<output>/
├── autograder.py
├── exercise_runtime_support/
└── exercises/<construct>/<exercise_key>/tests/
```

The teacher places this directory at
`<classroom>/autograders/<assignment>/` in the Classroom 50 repository and
commits it. Classroom 50's publish workflow materialises the per-assignment
archive from there. The builder performs no GitHub operation and creates no
archive.

Notebooks, solutions, `exercise.json`, teacher notes, and caches are never
copied into a bundle.

## Build workflow

1. Validate the exercise set and reject records with no canonical tests
   directory.
2. For each selected exercise, copy the hidden test modules and the
   exercise-local Python support files they reference.
3. Regenerate the bundle-local `exercise_runtime_support/` copy, so a change to
   that package is always followed by a rebuild.
4. Copy `scripts/autograder.py` to the bundle root.

The builder is generic: the exercise set is its input, and no construct or
exercise is special-cased.

## Local validation workflow

Validate before deploying:

```bash
uv run python scripts/build_classroom50_bundle.py \
  --source-root . \
  --exercise-set path/to/exercise-set.json \
  --runtime-source exercise_runtime_support \
  --output path/to/bundle

uv run python path/to/bundle/autograder.py \
  --student-root path/to/student-checkout \
  --result path/to/result.json \
  --variant solution
```

A full solution dry run confirms the bundle before deployment. A local mode run
installs nothing and uses the developer's own environment.

## Classroom 50 runtime workflow

1. The teacher commits the generated assignment directory to the Classroom 50
   repository.
2. The repository's publish workflow materialises and publishes the
   per-assignment archive.
3. A student accepts the assignment and receives the normal Classroom 50
   control files.
4. A later submission triggers the built-in runner.
5. The runner downloads and extracts the per-assignment bundle and invokes
   `autograder.py` with no arguments, from the student checkout.
6. The grader installs its test dependencies, forces the student notebook
   variant, runs the bundle's hidden tests against the checkout, and writes
   `./result.json`.
7. Classroom 50 validates and authoritatively re-stamps the result, derives the
   status, publishes the submission Release, and later collects scores.

The bundle is fetched on each grading run, so a committed bundle update does
not require a student-repository change.

## Assignment configuration

The assignment keeps `autograder: "default"`, uses autograded grading mode,
and carries no declarative `tests` block, `no_autograder`, or `empty_repo`. The
student repository is created from a template that provides
`exercise_metadata/`, the student notebooks, and the visible test copies that
the bundle deliberately excludes.

A Python 3.14 runtime is the Classroom 50 default and is sufficient.

## Result contract

The grader writes the canonical `classroom50/result/v1` fields, names each
case `<exercise_key>::<leaf-nodeid>`, and awards one point per passing case.
It exits zero for a completed run whether cases pass or fail, and non-zero
without a result when it cannot grade. Classroom 50 derives the commit status
and the Release from the validated result.

## Operational notes

- The grade job stops after 15 minutes, and a fetched bundle is capped at
  10 MiB. Keep an assignment's selected exercise set within both when
  choosing what to bundle.
- Pages/CDN propagation can take roughly ten minutes, so a submission in that
  window may fetch the previous bundle.
- Hidden tests are published through Pages, so a bundle must contain no
  solutions, credentials, or other confidential material. The visible test
  copies in the student template are the student-facing self-check surface;
  the bundle's copies are what the grader runs.

## Non-goals

This workflow does not add a GUI bundle importer, a `gh teacher` upload
command, classroom or roster automation, a live acceptance/submission/collection
pilot, or a new exercise, notebook, or sequencing workflow.
