---
name: classroom50-deploy
description: Use when preparing, registering, publishing, or verifying a Classroom 50 assignment that grades selected exercises from this repository with a teacher-side bundle. Guides the teacher through the staged deployment and its checks.
---

# Deploy a Classroom 50 exercise bundle

Use this workflow for an **individual assignment with an existing student template** and a per-assignment hidden grading bundle. The exercise selection is an input to the builder; it need not include every exercise in the template. Run commands from the exercise source repository root unless a command uses `git -C` or says otherwise. Use `uv` for Python work.

The supported builder and grader interface is [docs/developers/classroom50-autograder.md](../../../docs/developers/classroom50-autograder.md). The [Sequence first-three deployment record](../../../docs/teachers/classroom50-sequence-first-three-deployment-2026-09-30.md) is an example, not a reusable configuration or a live-grading success claim. Check the current Classroom 50 [teacher CLI guide](https://github.com/foundation50/classroom50/wiki/CLI-Teacher-Guide) if its commands change.

## Inputs and boundaries

Get the teacher's chosen organization, classroom short name, new assignment slug and display name, template `owner/repo`, and exact `(construct, exercise_key)` list. Establish whether the request is only to prepare a bundle or also to register and publish it. **Do not run assignment registration, commit, or push on a preparation-only request.** Stop at each gate if the evidence is missing or the teacher needs to decide the assessment scope. Never paste credentials into commands, logs, or bundles.

Set paths to a **new, dedicated** temporary working directory: the builder deletes its `--output` directory on each run. Replace every angle-bracket placeholder before running the recipes. Keep the exercise-set JSON and results outside both Git working trees. The `WORK` directory is an example location, not durable deployment storage.

```bash
ORG='<organization>'
CLASSROOM='<classroom-short-name>'
SLUG='<new-assignment-slug>'
NAME='<assignment-display-name>'
TEMPLATE='<owner/repository>'
WORK='/tmp/opencode/<unique-deployment-work-directory>'
PAGES_BASE_URL='https://<organization-pages-host>/classroom50'
SOURCE_ROOT="$(pwd)"
EXERCISE_SET="$WORK/exercise-set.json"
BUNDLE="$WORK/bundle"
RESULT="$WORK/solution-result.json"
CLONE="$WORK/classroom50"
PUBLISHED="$WORK/published.tar.gz"
mkdir -p "$WORK"
```

Record the selected values and the source revision in the deployment notes. Keep unrelated source-tree edits out of the Classroom 50 commit. If a required stage fails, fix that issue and repeat its checks before continuing; a prior pilot's case count or commit is not a pass criterion.

## 1. Inspect source, template, and access

```bash
git status --short --branch
git rev-parse HEAD
uv --version
gh --version
gh auth status
gh repo view "$TEMPLATE" --json nameWithOwner,isTemplate,isPrivate,defaultBranchRef,url
gh repo view "$ORG/classroom50" --json nameWithOwner,isPrivate,defaultBranchRef,url
gh extension list
```

Inspect `docs/teachers/construct-template-repos.md` as a pointer to existing construct templates, then verify the actual selected exercise directories and tests under `exercises/<construct>/<exercise_key>/`. Verify the template's **default branch** contains the selected canonical student notebooks and `exercise_metadata/`; compare its scope with the graded set. A template with more exercises than the bundle is acceptable when intentional. Do not create or sync a template as an incidental deployment step.

If `gh` cannot see the private organization repository, check which authentication source it selected. An environment `GITHUB_TOKEN` (or `GH_TOKEN`) can override the local `gh` login; a 404/403 under that token does not establish that the classroom is missing. If the local login is the authorized identity, repeat `gh` commands with the conflicting token unset (for example, `env -u GITHUB_TOKEN gh ...`) and use that identity consistently for the later push. Install the extension only if absent: `gh extension install foundation50/gh-teacher`. If it requests additional OAuth scopes, the teacher must run the indicated `gh auth refresh` interactively and verify access before proceeding; for the recorded pilot this was `gh auth refresh -h github.com -s admin:org,read:org,repo,workflow`.

**Gate:** The correct template, default branch, exercise source, teacher account, and existing classroom are identified. Record any source working-tree changes; do not overwrite them.

## 2. Select the graded exercises

Write `$EXERCISE_SET` as a JSON array of the chosen canonical keys, for example:

```json
[
  {"construct": "sequence", "exercise_key": "ex002_sequence_modify_basics"},
  {"construct": "sequence", "exercise_key": "ex003_sequence_modify_variables"}
]
```

This is **illustrative**, not the default selection. Confirm each selected exercise has canonical tests and the support files required by the current builder. It requires both `expectations.py` and `student_checker_support.py` for every selected exercise. A recorded all-Sequence attempt failed when ex011 lacked `expectations.py`; ex011 now has that file, but the historical failure does not establish that a current all-Sequence bundle passes. Run the build for the approved selection. Treat a missing file or failed build as a separate development issue, not a reason to change the builder while publishing an assignment.

**Gate:** The teacher has approved the exact graded set and understands any template/assignment scope difference.

## 3. Build and inspect the teacher-side bundle

```bash
uv run python scripts/build_classroom50_bundle.py \
  --source-root "$SOURCE_ROOT" \
  --exercise-set "$EXERCISE_SET" \
  --runtime-source "$SOURCE_ROOT/exercise_runtime_support" \
  --output "$BUNDLE"
rg --files --hidden --no-ignore "$BUNDLE"
```

Check that the root has `autograder.py` and `exercise_runtime_support/`, and that `exercises/` contains **only** the selected exercise directories. Inspect the **complete** `test_*.py` inventory and transitively copied support modules: the builder includes every test module in a selected exercise's tests directory, including any `test_repo_*.py` files. Decide whether those cases belong in the score before registering the assignment. Confirm there are no notebooks, solutions, `exercise.json`, teacher notes, cache files, or credentials. The published bundle is fetchable; hidden tests are tamper-resistant relative to student checkouts, not confidential.

**Gate:** The selected exercise directories, test modules, support files, and scoring scope match the teacher's intention.

## 4. Dry-run solutions, inspect the score, rebuild

The source checkout supplies canonical **solution** notebooks and `exercise_metadata/`. Supply both local-mode options; a no-argument invocation selects Classroom 50 mode, grades students, and installs grading dependencies into its interpreter.

```bash
uv run python "$BUNDLE/autograder.py" \
  --student-root "$SOURCE_ROOT" \
  --result "$RESULT" \
  --variant solution
uv run python -m json.tool "$RESULT"
```

Inspect `schema` (`classroom50/result/v1`), `score`, `max-score`, case rows and names, and the count per exercise. Require a nonempty full pass with the intended cases; do not hardcode a total from the Sequence pilot. A local result carries `local` identities and is **not** a submitted or collected classroom score. Review warnings rather than silently suppressing them. Student-variant failures in this repository are expected; this pre-deployment pass uses solutions.

Local grading can create `__pycache__` inside the bundle. Run the **same builder command from stage 3 again** immediately before deployment; it replaces its output. Reinspect the regenerated directory, including for cache files and unintended content. Rebuilding incorporates the current runtime source, so if sources changed after the dry run, repeat the solution check and rebuild again.

**Gate:** The solution result is a full pass for the approved inventory, and the freshly rebuilt copy is clean.

## 5. Register the assignment

Run this stage only when the teacher requested deployment. Check for the slug before adding it: re-running `assignment add` on an existing slug can rewrite its configuration and drop flags that are not repeated.

```bash
gh teacher assignment list "$ORG" "$CLASSROOM" --json
gh teacher assignment add "$ORG" "$CLASSROOM" "$SLUG" \
  --name "$NAME" --template "$TEMPLATE" --mode individual
gh teacher assignment list "$ORG" "$CLASSROOM" --json
```

If the slug exists, stop and review its configuration with the teacher instead of re-adding. Verify the new entry has the intended name, template at its default branch, individual mode, `autograder: "default"`, and no declarative `tests` block. The CLI adds the assignment but **does not upload the grading bundle**. Use the same authorized `gh` identity from stage 1 for these commands.

**Gate:** The saved assignment entry matches the approved inputs.

## 6. Place, review, commit, and push the override

Clone the organization's config repository separately; confirm its branch, clean status, and absence of a pre-existing override before copying. Never replace an existing override without reviewing it and explicitly agreeing on the update.

```bash
gh repo clone "$ORG/classroom50" "$CLONE"
git -C "$CLONE" status --short --branch
git -C "$CLONE" log --oneline -10
git -C "$CLONE" branch --show-current
git -C "$CLONE" branch -vv
ls "$CLONE/$CLASSROOM"
mkdir -p "$CLONE/$CLASSROOM/autograders/$SLUG"
cp -a "$BUNDLE/." "$CLONE/$CLASSROOM/autograders/$SLUG/"
git -C "$CLONE" status --short --branch
git -C "$CLONE" diff
git -C "$CLONE" add "$CLASSROOM/autograders/$SLUG"
git -C "$CLONE" diff --cached --stat
git -C "$CLONE" diff --cached --name-only
git -C "$CLONE" diff --cached
git -C "$CLONE" diff --cached --check
git -C "$CLONE" status --short --branch
```

Review the staged **contents**, not just the filenames: check for secrets, notebooks, solutions, caches, and unrelated changes. Confirm the staged paths are exclusively under `<classroom>/autograders/<slug>/` and the bundle contents sit directly inside that directory (no extra `bundle/` layer). Before committing inspect status, diff, and recent log as above. Commit and push only after the teacher has requested publication; use the clone's verified tracking branch, not a guessed branch name.

```bash
git -C "$CLONE" commit -m "[Classroom 50] autograder: add $SLUG bundle"
git -C "$CLONE" push origin "$(git -C "$CLONE" branch --show-current)"
git -C "$CLONE" status --short --branch
git -C "$CLONE" rev-parse HEAD
```

**Gate:** The pushed commit contains only the approved override and the clone tracks the expected branch with no leftover changes.

## 7. Verify the published archive

```bash
gh api "repos/$ORG/classroom50/contents/$CLASSROOM/autograders/$SLUG/autograder.py" --jq '.size'
gh run list -R "$ORG/classroom50" --workflow publish-pages.yaml --limit 10 \
  --json databaseId,status,conclusion,headSha,url
```

Match a `Publish Pages` run's `headSha` to the commit from stage 6, then watch **that run**:

```bash
gh run watch <matching-run-id> -R "$ORG/classroom50" --exit-status
curl -fsSL --retry 2 --retry-delay 2 \
  "$PAGES_BASE_URL/$CLASSROOM/autograders/$SLUG.tar.gz" -o "$PUBLISHED"
tar -tzf "$PUBLISHED"
stat -c %s "$PUBLISHED"
mkdir -p "$WORK/published-unpacked"
tar -xzf "$PUBLISHED" -C "$WORK/published-unpacked"
diff -qr "$BUNDLE" "$WORK/published-unpacked/$SLUG"
```

Inspect the actual Pages-served archive: it must have a top-level `<slug>/` containing `autograder.py`, the runtime, and **only** the approved hidden exercise files. Extract only after inspecting its listing; compare its contents to the rebuilt bundle. Check for caches and unwanted content, and ensure the fetched bundle stays under Classroom 50's 10 MiB limit. Pages/CDN updates can lag; if the served archive is stale, retry verification rather than assuming a green workflow means the latest bundle is live. A later grading-source change requires a new build, publication, and archive check.

**Gate:** The exact pushed commit published successfully and the downloadable archive matches the approved bundle.

## 8. Report deployment versus live grading

Record the selected exercise keys, template default branch, observed case counts and solution score, assignment entry, bundle commit, Pages run, archive URL, and any warnings or unresolved issues. State precisely which evidence is local and which is published. Do not describe this as end-to-end student grading without a student submission.

For a separate live pilot, have an appropriate student or authorized staff account accept the assignment, submit its checkout, inspect the grading run and submission Release's `result.json`, then collect scores for that assignment if needed:

```bash
gh workflow run collect-scores.yaml --repo "$ORG/classroom50" \
  -f classroom="$CLASSROOM" -f assignment="$SLUG"
```

Verify the collected result rather than inferring it from publication. These steps require the student's or staff tester's own account/repository and were **not** performed in the Sequence first-three deployment record.
