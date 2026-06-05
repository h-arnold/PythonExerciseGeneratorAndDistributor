# Creating Template Repositories for GitHub Classroom

This guide explains how to turn a set of Python exercises into a **template repository** on GitHub. A template repository is a special kind of repository that you use as a starting point for GitHub Classroom assignments. Once you create one, students get a copy with their own workspace when they accept the assignment.

> **Full reference:** If you need details on every possible flag and option, see the developer guide at [`docs/developers/template_repo_cli.md`](../developers/template_repo_cli.md).

## What you will need

- **Python exercises already created** in this repository (or you can use the ones that come with it).
- **The `gh` (GitHub CLI) tool**. This is already installed in your Codespace — you do not need to install it separately.
- **A GitHub account**, signed into GitHub in your browser.

## Before you start: authenticate with GitHub

When your Codespace starts, it automatically gets a temporary token that only has permission to work with *this* repository. To create template repositories in your own account or an organisation, you need to authenticate with your full GitHub account first.

Open the **Terminal** (`Ctrl + `` ` or **Terminal > New Terminal** from the menu) and run these two commands, one at a time:

```bash
unset GITHUB_TOKEN
gh auth login
```

The first line clears the temporary token. The second starts the GitHub authentication process — follow the on-screen instructions (choose "Login with a browser" if prompted, then enter the code shown in the terminal on the GitHub website).

> **Why is this needed?** When a GitHub Codespace starts, it sets a `GITHUB_TOKEN` environment variable with permissions limited to just that Codespace's repository. This token cannot create new repositories in your account or organisation. Running `unset GITHUB_TOKEN` removes that restricted token, and `gh auth login` lets you sign in with your own credentials so the CLI has the permissions it needs.

---

## Creating a template repository

### The simplest way: all exercises from one topic

This command bundles every exercise from the `sequence` topic into a new template repository called `sequence-exercises`:

```bash
template_repo_cli create --construct sequence --repo-name sequence-exercises
```

After it finishes, you will have a new repository on GitHub. It will be public and marked as a template — ready to use in GitHub Classroom.

### Choosing exercises by type

You can narrow the selection to only `modify` exercises (or only `debug` or `make`):

```bash
template_repo_cli create \
  --construct sequence \
  --type modify \
  --repo-name sequence-modify
```

### Choosing specific exercises

If you want only a handful of specific exercises:

```bash
template_repo_cli create \
  --exercise-keys ex002_sequence_modify_basics ex003_sequence_modify_variables \
  --repo-name getting-started
```

### Putting the repository in a GitHub organisation (optional)

If your school uses a GitHub organisation to organise repositories, add the `--org` flag:

```bash
template_repo_cli create \
  --construct sequence \
  --repo-name sequence-exercises \
  --org my-school-organisation
```

Replace `my-school-organisation` with your organisation's GitHub name. If you do not need an organisation, just leave this flag out — the repository will be created in your personal account.

### Other useful options

| Option | What it does |
|---|---|
| `--name "My Title"` | Sets a human-readable title for the README (instead of the repo name). |
| `--private` | Makes the repository private (not visible to the public). Useful for draft assignments. |
| `--dry-run` | Tests the packaging without actually creating the repository. Use this to preview what would be included. |

### Putting it all together — a realistic example

```bash
template_repo_cli create \
  --construct sequence selection \
  --type modify \
  --repo-name week1-python \
  --name "Week 1: Sequence and Selection" \
  --org my-school-org
```

This creates a template called `week1-python` in the `my-school-org` organisation, containing all `modify` exercises from the `sequence` and `selection` topics.

---

## Updating an existing template repository

If you have already created a template and want to refresh it (for example, you fixed a typo in an exercise), use the `update-repo` command:

```bash
template_repo_cli update-repo \
  --construct sequence \
  --repo-name my-org/sequence-exercises
```

This force-pushes the latest version of the exercises into the existing repository. Students who already accepted the assignment will keep their work — only the template itself is updated.

---

## Checking what exercises are available

To see a list of every exercise in the repository:

```bash
template_repo_cli list
```

To see only exercises in a specific topic:

```bash
template_repo_cli list --construct sequence
```

---

## What happens next

1. Your template repository is now on GitHub.
2. Go to **GitHub Classroom**, create a new assignment, and choose "Import from a template repository".
3. Select the repository you just created.
4. Students accept the assignment and get their own copy with the exercises ready to go.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `gh: not found` | Contact your IT coordinator — the GitHub CLI needs to be installed. In Codespaces it should already be available. |
| Authentication fails | Run `unset GITHUB_TOKEN` then `gh auth login` again — see the [Before you start](#before-you-start-authenticate-with-github) section above. |
| "No exercises found" | Check your spelling: construct names are lowercase (e.g., `sequence`, not `Sequence`). |
| Want to check before creating | Add `--dry-run` to preview without actually creating anything. |

> **Need more detail?** The full CLI reference (all flags, options, and technical details) is at [`docs/developers/template_repo_cli.md`](../developers/template_repo_cli.md).
