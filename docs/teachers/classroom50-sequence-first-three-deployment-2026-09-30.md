# Classroom 50 Sequence pilot: deployment record (30 September 2026)

This is a record of **what we actually did** to register and publish the first
three Sequence exercises in Classroom 50 on 30 September 2026. It is a snapshot
for evaluating and improving the process after a live submission, not a claim
that end-to-end student grading has already succeeded. For the supported
builder and grader interfaces, see the
[Classroom 50 autograder contract](../developers/classroom50-autograder.md).

## Outcome and identities

| Item | Value |
| --- | --- |
| Exercise source | This repository, `exercises/sequence/` |
| Existing student template | [`h-arnold/python-exercises-sequence`](https://github.com/h-arnold/python-exercises-sequence), default branch `main`; publicly visible and marked as a GitHub template |
| Classroom 50 organization | `Bassaleg-School` |
| Classroom short name | `9b-computer-science-2026-2029` |
| New assignment slug | `sequence-first-three` |
| Assignment display name | `Sequence: First Three Exercises` |
| Assignment configuration | Individual, template `h-arnold/python-exercises-sequence@main`, `autograder: "default"`, no declarative `tests` block |
| Selected exercises | `ex002_sequence_modify_basics`, `ex003_sequence_modify_variables`, `ex004_sequence_debug_syntax` |
| Local solution dry run | **97/97** collected cases passed; 67 pytest warnings |
| Bundle commit in the Classroom 50 repository | [`e1c03d7`](https://github.com/Bassaleg-School/classroom50/commit/e1c03d7d5147f832ae002cddc0ae020a76a2ad74) |
| Pages publication | [Publish Pages run 36683755740](https://github.com/Bassaleg-School/classroom50/actions/runs/36683755740), successful |
| Published archive | [`sequence-first-three.tar.gz`](https://bassaleg-school.github.io/classroom50/9b-computer-science-2026-2029/autograders/sequence-first-three.tar.gz), downloaded and inspected |

**Important scope distinction:** the existing Sequence template contains **14**
exercises. We did not make a new three-exercise template. Student repositories
created from this template contain all 14, but this assignment's hidden bundle
discovers and scores only the three exercises listed above. The grader uses the
bundle's tests, not student-visible test copies in the checkout.

Paths under `/tmp/opencode/` below were local, temporary working artefacts in
this session. They are not committed exercise-set configuration or durable
deployment storage. Substitute your own locations when repeating the steps.

## Chronological procedure

### 1. Inspect the exercise source, template and environment

We read the generated [construct template list](construct-template-repos.md),
which linked the Sequence template above and reported 14 exercises. We
confirmed the 14 canonical exercise directories under
`exercises/sequence/<exercise_key>/` and checked their exercise-local tests.
The following check confirmed the existing repository was public, was a
template, and used `main`:

```bash
gh repo view h-arnold/python-exercises-sequence \
  --json nameWithOwner,isTemplate,isPrivate,defaultBranchRef,url
```

We **did not** run `repoman create` or change the template.

The developer environment had `uv 0.12.14`, `gh 2.100.0`, and an existing
`.venv`. Python commands were run through `uv`. We checked `git status` before
working; the generated `docs/teachers/construct-template-repos.md` already had
a modified timestamp. We did not include unrelated source-repository changes
in the deployment commit.

### 2. First attempt: all 14 Sequence exercises (abandoned)

Initially we prepared `/tmp/opencode/sequence-exercise-set.json` listing all
14 Sequence exercise keys, `ex002` through `ex015` (the full names are the
canonical directory names under `exercises/sequence/`). From the **exercise
source repository root**, we tried:

```bash
uv run python scripts/build_classroom50_bundle.py \
  --source-root . \
  --exercise-set /tmp/opencode/sequence-exercise-set.json \
  --runtime-source exercise_runtime_support \
  --output /tmp/opencode/sequence-grading-bundle
```

The build stopped at `ex011_sequence_gaps_consolidation` with
`FileNotFoundError: Required hidden file 'expectations.py' not found for
'ex011_sequence_gaps_consolidation'`. That exercise's tests directory had
`student_checker_support.py` and a test module, but **no** `expectations.py`;
its tests contain their expected values inline. The builder at that time
required `expectations.py` and `student_checker_support.py` for every selected
exercise, even if its tests did not need both.

During investigation we temporarily changed the builder to include documented
support files only when present, added a regression test, and edited the
builder documentation. The first targeted test run failed because our
synthetic test fixture still *explicitly referenced* the missing support
module. After adjusting the fixture to use an inline expectation, the targeted
builder/docs tests passed, Ruff passed, and the 14-exercise build succeeded.
An all-14 **local solution** dry run then reported **392 passed, 267 warnings**.
This exploratory fix was **reverted** when we narrowed the scope. It is **not**
in this repository's deployed three-exercise bundle and should not be treated
as a completed fix for future all-Sequence deployments. The wider dry-run
result was not used as the pilot's score.

### 3. Select only the first three and build with the original builder

At the teacher's request we stopped work on the full set, restored our interim
builder/test/documentation edits, and created
`/tmp/opencode/sequence-first-three.json` with these exact contents:

```json
[
  {"construct": "sequence", "exercise_key": "ex002_sequence_modify_basics"},
  {"construct": "sequence", "exercise_key": "ex003_sequence_modify_variables"},
  {"construct": "sequence", "exercise_key": "ex004_sequence_debug_syntax"}
]
```

From the **exercise source repository root** we ran:

```bash
uv run python scripts/build_classroom50_bundle.py \
  --source-root . \
  --exercise-set /tmp/opencode/sequence-first-three.json \
  --runtime-source exercise_runtime_support \
  --output /tmp/opencode/sequence-first-three-bundle
```

This build completed successfully using the unchanged builder. We inspected
the bundle and verified its root contained `autograder.py`,
`exercise_runtime_support/`, and `exercises/sequence/` with only the selected
exercise directories. It had **five** `test_*.py` modules: the three canonical
exercise tests plus `test_repo_task_metadata.py` and
`test_repo_reporting_parity.py` from ex002. The builder includes every
`test_*.py` in each selected exercise's tests directory, including those two
repository-only checks. It also copied each selected exercise's
`expectations.py` and `student_checker_support.py` and ex002's transitively
referenced `framework_support.py`. We confirmed the bundle had **no notebooks
or solutions**. The teacher-side bundle is separate from the student template.

### 4. Validate the small bundle locally against solutions

From the **exercise source repository root**:

```bash
uv run python /tmp/opencode/sequence-first-three-bundle/autograder.py \
  --student-root /workspaces/PythonExerciseGeneratorAndDistributor \
  --result /tmp/opencode/sequence-first-three-solution-result.json \
  --variant solution
```

Here `--student-root` points at the source checkout because it has the
canonical **solution** notebooks and `exercise_metadata/`. The local invocation
needs both `--student-root` and `--result`; `--variant solution` is what selects
solutions. Classroom 50's eventual no-argument invocation instead forces the
**student** variant, runs from a student checkout, installs `pytest` and
`tabulate` into its grading interpreter, and writes `./result.json` there. Do
not use that no-argument invocation for a normal local pre-deployment check.

The command completed, and `/tmp/opencode/sequence-first-three-solution-result.json`
had `schema: "classroom50/result/v1"`, `score: 97`, `max-score: 97`, and 97
case rows. The rows were distributed **34 for ex002, 23 for ex003, and 40 for
ex004**. The JSON identity values were deliberately local (`classroom` and
`assignment` were `local`); this is **not** a submitted or collected Classroom
50 score. The run emitted **67 warnings**, mainly `PytestUnknownMarkWarning`
for `pytest.mark.task`, plus an already-imported plugin assertion-rewrite
warning. The warnings did not change the 97/97 result; we did not silence or
modify them.

That dry run created `__pycache__` directories inside the temporary bundle.
Before deployment, we ran the **same builder command from step 3 again**;
the builder deletes and regenerates its output directory. A check for
`**/__pycache__/*` then found none. We deployed this **fresh rebuild**, not
the cache-bearing dry-run directory as it stood immediately after grading.

### 5. Check Classroom 50 access and register the assignment

At first `gh extension list` showed no teacher extension, and the environment
provided a `GITHUB_TOKEN` associated with the `h-arnold` account. With that
environment token, private `Bassaleg-School/classroom50` lookups returned
404 and an organization membership lookup returned 403. This was an access
problem with the **token being selected**, not evidence that the organization
or classroom was absent. Running `gh` with `GITHUB_TOKEN` unset used the
locally configured `gh` login instead; that login could view the private
`classroom50` repository, showed admin access to it, and showed active admin
organization membership. The target classroom's `assignments.json` initially
contained an empty assignments array.

We installed the official teacher extension:

```bash
env -u GITHUB_TOKEN gh extension install foundation50/gh-teacher
```

The first attempt to add the assignment stopped before writing anything:
the local OAuth login lacked `admin:org`. The CLI gave the needed
`gh auth refresh` command. The teacher ran this **interactively** and
authorized it in GitHub:

```bash
env -u GITHUB_TOKEN gh auth refresh -h github.com -s admin:org,read:org,repo,workflow
```

We confirmed `gh auth status` reported `admin:org` afterwards, then ran:

```bash
env -u GITHUB_TOKEN gh teacher assignment add \
  Bassaleg-School 9b-computer-science-2026-2029 sequence-first-three \
  --name "Sequence: First Three Exercises" \
  --template h-arnold/python-exercises-sequence
```

The CLI reported that it added the assignment in
`Bassaleg-School/classroom50/9b-computer-science-2026-2029/assignments.json`
with template `h-arnold/python-exercises-sequence@main` and autograder
`default`. Verification:

```bash
env -u GITHUB_TOKEN gh teacher assignment list \
  Bassaleg-School 9b-computer-science-2026-2029 --json
```

The saved entry had slug `sequence-first-three`, the chosen name and template,
`mode: "individual"`, `autograder: "default"`, and `feedback_pr: true`; it had
**no declarative tests**. `gh teacher assignment add` registered the
assignment but **did not upload our grading bundle**. A direct check for the
per-assignment `autograder.py` in the remote repository returned 404 until
the next step. We did not invite students or accept the assignment at this
point.

### 6. Copy, commit and push the teacher-side bundle

We cloned the organization config repository into a separate directory (so
the unrelated working-tree changes in the exercise source repository were not
part of the deployment):

```bash
env -u GITHUB_TOKEN gh repo clone \
  Bassaleg-School/classroom50 /tmp/opencode/classroom50
```

The clone was clean on `main`, following `origin/main`; its most recent commit
was the CLI's assignment registration, `d1f717f`. We inspected the clone's
status, diff, recent log and the classroom directory. There was no existing
`autograders/sequence-first-three/` directory. After confirming the parent
directory, we copied the **contents** of the rebuilt bundle into the exact
per-assignment override path:

```bash
mkdir -p /tmp/opencode/classroom50/9b-computer-science-2026-2029/autograders/sequence-first-three
cp -a /tmp/opencode/sequence-first-three-bundle/. \
  /tmp/opencode/classroom50/9b-computer-science-2026-2029/autograders/sequence-first-three/
```

From **`/tmp/opencode/classroom50`** we staged only that directory and
reviewed the staged paths, diff summary, whitespace check, status, and recent
commit style before committing:

```bash
git add 9b-computer-science-2026-2029/autograders/sequence-first-three
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
git status --short --branch
git log --oneline -10
git commit -m "[Classroom 50] autograder: add sequence-first-three bundle"
env -u GITHUB_TOKEN git push origin main
```

The commit was [`e1c03d7`](https://github.com/Bassaleg-School/classroom50/commit/e1c03d7d5147f832ae002cddc0ae020a76a2ad74)
and changed **only 37 files** under
`9b-computer-science-2026-2029/autograders/sequence-first-three/` (grader,
runtime, three exercises' hidden test and support files). The staged diff
check found no whitespace errors. We checked the bundle for obvious token
and private-key patterns before copying it; no matches were found. The push
updated `main` from `d1f717f` to `e1c03d7`; the separate clone was clean and
tracking `origin/main` afterwards. No notebook, solution, student template,
metadata file, or unrelated exercise-source working-tree edit was staged or
committed as part of this deployment.

### 7. Verify GitHub and the published archive

The GitHub Contents API returned the newly committed
`9b-computer-science-2026-2029/autograders/sequence-first-three/autograder.py`
(size **16,581 bytes**). We observed a `Publish Pages` workflow run for the
exact commit, then waited for it:

```bash
env -u GITHUB_TOKEN gh run list -R Bassaleg-School/classroom50 \
  --workflow publish-pages.yaml --limit 5 \
  --json databaseId,status,conclusion,headSha,createdAt,url
env -u GITHUB_TOKEN gh run watch 36683755740 \
  -R Bassaleg-School/classroom50 --exit-status
```

Run [36683755740](https://github.com/Bassaleg-School/classroom50/actions/runs/36683755740)
finished **successfully** with head SHA
`e1c03d7d5147f832ae002cddc0ae020a76a2ad74`. The repository's
`.github/workflows/publish-pages.yaml` packages each
`<classroom>/autograders/<slug>/` directory as
`<classroom>/autograders/<slug>.tar.gz`; the archive contains a top-level
`<slug>/` directory so the Classroom 50 runner can extract and locate its
`autograder.py`.

We then fetched the **actual Pages-served archive**, rather than inferring
publication solely from a green workflow:

```bash
curl -fsSL --retry 2 --retry-delay 2 \
  https://bassaleg-school.github.io/classroom50/9b-computer-science-2026-2029/autograders/sequence-first-three.tar.gz \
  -o /tmp/opencode/sequence-first-three-published.tar.gz
tar -tzf /tmp/opencode/sequence-first-three-published.tar.gz
```

The download succeeded. Its listing began with `sequence-first-three/` and
included `autograder.py`, `exercise_runtime_support/`, and only the selected
ex002–ex004 exercise tests/support files, with no cache directories. The
downloaded compressed archive was about **32 KiB**, below Classroom 50's
10 MiB fetched-bundle limit. A future bundle change must be rebuilt, committed
and republished; merely changing the exercise source or the student template
does not update this teacher-side archive.

## Issues, decisions and unfinished validation

1. **All-14 builder failure:** ex011 lacks `expectations.py`; the original
   builder requires it. The temporary optional-file experiment was reverted.
   This issue needs separate investigation before building an assignment that
   includes ex011.
2. **Bundled repository-only checks:** ex002 contributed two `test_repo_*.py`
   modules because the builder includes all `test_*.py` files. They are part
   of the **97-case** observed score. Review their grading relevance before
   using this pilot as a final assessment; do not assume only the three
   `test_ex...py` modules were shipped.
3. **Warnings:** the small solution dry run passed but emitted 67 warnings,
   predominantly unknown `task` marks. We did not treat these as failures or
   suppress them. A Classroom 50 runner invocation may have different warning
   presentation than the local dry run.
4. **Two GitHub identities in one shell:** an environment `GITHUB_TOKEN` could
   not see the private Classroom 50 repository. `env -u GITHUB_TOKEN` selected
   the usable locally authenticated `gh` login. The teacher extension also
   needed an interactive `admin:org` OAuth scope refresh. Do not paste tokens
   into commands, documentation or the published bundle.
5. **Bytecode generated by local grading:** rebuilding the temporary bundle
   immediately before copying removed `__pycache__` from the published copy.
6. **Template/assignment scope mismatch is deliberate for this pilot:** the
   starter template contains 14 exercises while this assignment grades three.
   If later assignments select other exercises, build and publish a matching
   bundle for each assignment rather than assuming this bundle grades all 14.
7. **Live-run gap:** we confirmed source-solution grading, assignment
   registration, the committed bundle, successful Pages publication, and the
   downloadable archive. We **did not** create a student repository, accept
   the assignment, submit a student checkout, see a no-argument grader run on
   Classroom 50, verify a submission Release's `result.json`, or collect a
   score. The next pilot should check those steps before describing this as
   end-to-end validated. Actual acceptance and submission require the
   student's account and repository. The published archive is fetched afresh
   for grading, although Pages/CDN updates can lag by about ten minutes.

Once appropriate, the Classroom 50 accept command for this assignment would
be (it was **not run** during this deployment):

```bash
gh student accept Bassaleg-School 9b-computer-science-2026-2029 sequence-first-three
```

For scoring and invocation details see the
[autograder contract](../developers/classroom50-autograder.md). For the upstream
CLI's assignment and publish behaviour see Classroom 50's
[teacher CLI guide](https://github.com/foundation50/classroom50/wiki/CLI-Teacher-Guide),
[`gh teacher` reference](https://github.com/foundation50/classroom50/wiki/gh-teacher),
and [advanced autograding guide](https://github.com/foundation50/classroom50/wiki/Advanced-Autograding).
