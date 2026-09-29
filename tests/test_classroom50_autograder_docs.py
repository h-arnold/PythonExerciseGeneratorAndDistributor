"""Documentation-contract tests for the generic Classroom 50 grading contract.

Two groups of checks live here.

The scoring-contract tests keep ``docs/developers/classroom50-autograder.md``
aligned with the generic grading contract, re-derive the Selection pilot counts
and titles from canonical sources, and fail fast if the document is missing.

The invocation-contract tests cover the Stage 2 documentation surface: the
no-argument Classroom 50 mode, the local dry run, the canonical result field
names, and the build -> place -> commit deployment workflow. They read prose
rather than exact sentences, so a reviewer can phrase the same fact differently,
but they fail when a required part of the contract is absent or stale. Every
check is offline, deterministic, and reads only repository files.

Contract source: ``SPEC.md`` and ``WORKFLOW_SPEC.md`` for the behaviour,
``ACTION_PLAN.md`` Stage 2 for the documentation surface, with the Selection
pilot as builder configuration/validation fixture.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "developers" / "classroom50-autograder.md"
SELECTION_DIR = REPO_ROOT / "exercises" / "selection"

# The documents Stage 2 may touch: the contract guide plus the four guides that
# cross-reference it. The invocation contract is checked on the guide; the stale
# wording and link checks sweep all five so a second document cannot reintroduce
# a withdrawn requirement.
AFFECTED_DOCS: tuple[Path, ...] = (
    DOC_PATH,
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "docs" / "developers" / "execution-model.md",
    REPO_ROOT / "docs" / "developers" / "development.md",
    REPO_ROOT / "docs" / "developers" / "project-structure.md",
)
# The runner variables the Classroom 50 mode reads, with the two identity
# variables that are optional or have a fallback.
RUNNER_IDENTITY_VARIABLES: tuple[str, ...] = (
    "CLASSROOM",
    "ASSIGNMENT",
    "ASSIGNMENT_TYPE",
    "SUBMISSION_TAG",
    "COMMIT_URL",
    "RELEASE_URL",
    "OWNER",
    "REVIEW_URL",
)
SUPPORTED_ASSIGNMENT_TYPES = ("individual", "group", "team")
# The bundle destination the teacher commits into the Classroom 50 repository.
BUNDLE_DESTINATION = "<classroom>/autograders/<assignment>/"
# The two local dry-run options, which the grader requires as a pair.
LOCAL_MODE_OPTIONS = ("--student-root", "--result")
# The CLI entry points the guide documents; a doc update must not invent one.
DOCUMENTED_ENTRY_POINTS = ("scripts/build_classroom50_bundle.py", "scripts/autograder.py")
# Requirements withdrawn from ``SPEC.md`` by the current revision. Naming any of
# them in a directly affected document would reintroduce a dependency this
# repository deliberately dropped.
WITHDRAWN_TERMS: tuple[str, ...] = (
    "manifest",
    "bootstrap",
    "fresh-install",
    "trust boundary",
    "checksum",
    "snapshot",
    "package-origin",
    "assignment-schema",
    "assignment schema test matrix",
    "gh teacher",
)
# Wording that makes the absence of a field explicit rather than describing it.
_REMOVAL_MARKERS = (
    "removed",
    "no longer",
    "superseded",
    "replaced",
    "renamed",
    "must not",
    "not used",
    "without",
)
_LOCAL_PAIR_PHRASES = (
    "as a pair",
    "together",
    "in pairs",
    "both are required",
    "both must",
    "neither option",
    "neither of the local",
)
# How a document may word "the totals are derived by adding up the rows".
_DERIVATION_PHRASES = ("sum", "total", "aggregate", "count of")
# What the totals are derived from: the per-case rows, not the pilot counts.
_ROW_PHRASES = ("row", "case", "per-case", "per case")
# The two ways a document can say one local option alone is rejected, in either
# word order, so "only `--student-root` ... is a usage error" and
# "a usage error ... `--result` without `--student-root`" both match.
_SINGLE_OPTION_SUBJECT = (
    r"(?:`?--(?:student-root|result)`?|only one of (?:them|these|the two)"
    r"|either (?:local )?option|one of the (?:local )?options)"
)
_SINGLE_OPTION_FAILURE = (
    r"(?:usage error|rejected|not accepted|is an error|is invalid|invalid usage)"
)
_SINGLE_OPTION_ERROR_RES = (
    re.compile(rf"{_SINGLE_OPTION_SUBJECT}[^.\n]{{0,100}}?{_SINGLE_OPTION_FAILURE}", re.IGNORECASE),
    re.compile(rf"{_SINGLE_OPTION_FAILURE}[^.\n]{{0,100}}?{_SINGLE_OPTION_SUBJECT}", re.IGNORECASE),
)
_NO_LOCAL_INSTALL_PHRASES = (
    "installs nothing",
    "installs no",
    "does not install",
    "never installs",
    "without installing",
    "no install",
)
_NON_UPLOADABLE_PHRASES = (
    "not uploadable",
    "non-uploadable",
    "never uploaded",
    "cannot be uploaded",
    "never evidence",
)
_SUPERSEDED_RESULT_FIELDS = ("version", "name")
_PROXIMITY_WINDOW = 140

# Pinned pilot expectations (SPEC.md). The collected-count test below
# re-derives these from real pytest collection so the pins cannot drift
# silently from the canonical test sources.
EXPECTED_KEYS: tuple[str, ...] = (
    "ex001_selection_modify_basics",
    "ex002_selection_debug_if_then_else",
    "ex003_selection_modify_elif_boundaries",
    "ex004_selection_modify_logical_operators",
)
EXPECTED_COUNTS: dict[str, int] = {
    "ex001_selection_modify_basics": 33,
    "ex002_selection_debug_if_then_else": 60,
    "ex003_selection_modify_elif_boundaries": 60,
    "ex004_selection_modify_logical_operators": 71,
}
EXPECTED_TITLES: dict[str, str] = {
    "ex001_selection_modify_basics": "Selection Modify Basics",
    "ex002_selection_debug_if_then_else": "Selection Debug If Then Else",
    "ex003_selection_modify_elif_boundaries": (
        "Selection Modify: Elif Chains, Boundaries and Constants"
    ),
    "ex004_selection_modify_logical_operators": "Selection Modify Logical Operators",
}
EXPECTED_TOTAL = 224

_COLLECT_LINE_RE = re.compile(r"^(?P<path>.+?): (?P<count>\d+)\s*$")
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
# A superseded result field only counts as stale when it is presented as a field
# name, i.e. quoted or in a code span, and not in a sentence that says it is gone.
_QUOTED_FIELD_TEMPLATE = r"[`\"]{field}[`\"]"
# A result field is documented the way the payload names it: a key in a code span
# or in quotes. Requiring the delimiter keeps unrelated prose ("a full pass",
# "score collection", "schema of the bundle") from satisfying the contract.
_RESULT_FIELD_TEMPLATE = r"[`\"']{field}[`\"']"


def _read(path: Path) -> str:
    """Read a repository document, failing fast when it is absent."""
    assert path.is_file(), f"Documentation file missing: {path.relative_to(REPO_ROOT)}"
    return path.read_text(encoding="utf-8")


def _read_doc() -> str:
    """Read the autograder contract doc, failing fast if it is absent."""
    return _read(DOC_PATH)


def _normalised(text: str) -> str:
    """Return the text lowercased with runs of whitespace collapsed to one space."""
    return " ".join(text.lower().split())


def _mentions(text: str, *phrases: str) -> bool:
    """Return whether any phrase appears anywhere in the normalised text."""
    lowered = _normalised(text)
    return any(_normalised(phrase) in lowered for phrase in phrases)


def _near(text: str, anchor: str, *related: str, window: int = _PROXIMITY_WINDOW) -> bool:
    """Return whether any ``related`` phrase appears close to ``anchor``.

    Documentation states one fact per sentence or bullet, so this checks that
    two pieces of wording belong to the same neighbourhood instead of anywhere
    in the document. Prose can be rephrased freely; the association cannot.
    """
    lowered = _normalised(text)
    related_phrases = tuple(_normalised(phrase) for phrase in related)
    for match in re.finditer(re.escape(_normalised(anchor)), lowered):
        start = max(0, match.start() - window)
        neighbourhood = lowered[start : match.end() + window]
        if any(phrase in neighbourhood for phrase in related_phrases):
            return True
    return False


def _contexts_of(text: str, anchor: str) -> list[str]:
    """Return the normalised sentence, bullet, or table cell that contains ``anchor``.

    A single clause carries one fact in documentation, so sentence scoping is
    the tightest association that still allows the wording to be rephrased.
    """
    target = _normalised(anchor)
    return [
        _normalised(part) for part in re.split(r"[.;:\n|]", text) if target in _normalised(part)
    ]


def _documents_result_field(text: str, field: str) -> bool:
    """Return whether ``field`` is presented as a key of the result document."""
    return re.search(_RESULT_FIELD_TEMPLATE.format(field=re.escape(field)), text) is not None


def _canonical_test_file(exercise_key: str) -> Path:
    return SELECTION_DIR / exercise_key / "tests" / f"test_{exercise_key}.py"


def _exercise_titles() -> dict[str, str]:
    """Derive the exact Selection titles from the canonical exercise.json sources."""
    titles: dict[str, str] = {}
    for key in EXPECTED_KEYS:
        metadata_path = SELECTION_DIR / key / "exercise.json"
        assert metadata_path.is_file(), f"Canonical metadata missing: {metadata_path}"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        titles[key] = metadata["title"]
    return titles


def _collected_counts() -> dict[str, int]:
    """Derive per-exercise collected pytest counts via collection only.

    Runs pytest with `--collect-only` (no test is executed, no notebooks run,
    no network): the count per file is the number of collected cases, which
    includes parametrize expansion that a plain `def test_` count would miss.
    """
    counts: dict[str, int] = {}
    for key in EXPECTED_KEYS:
        test_file = _canonical_test_file(key)
        assert test_file.is_file(), f"Canonical test file missing: {test_file}"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                str(test_file),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert proc.returncode == 0, f"Collection failed for {key}:\n{proc.stderr}"
        match = _COLLECT_LINE_RE.match(proc.stdout.strip().splitlines()[-1])
        assert match is not None, f"Unparseable collect output for {key}:\n{proc.stdout}"
        counts[key] = int(match.group("count"))
    return counts


def _documented_count(doc: str, exercise_key: str) -> int:
    """Extract the case count from the documentation row for one exercise."""
    for line in doc.splitlines():
        if exercise_key not in line:
            continue
        matches = re.findall(r"(?<!\d)(\d{1,3})(?!\d)", line.replace(exercise_key, ""))
        if len(matches) == 1:
            return int(matches[0])
    raise AssertionError(f"Contract must document one case count for {exercise_key}")


def test_contract_doc_exists() -> None:
    assert DOC_PATH.is_file(), (
        "Stage 3 deliverable missing: docs/developers/classroom50-autograder.md does not exist"
    )


def test_scoring_one_point_per_case() -> None:
    doc = _normalised(_read_doc())
    assert "one point per passing pytest case" in doc, (
        "Contract must state one point per passing pytest case"
    )


def test_per_test_names_exact_leaf_nodeid() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    assert "<exercise_key>::" in doc.replace(" ", ""), (
        "Contract must name per-test results as <exercise_key>::<leaf-nodeid>"
    )
    assert "test_*.py::test_name" in doc, (
        "Contract must define the leaf nodeid as test_*.py::test_name"
    )
    assert "no absolute paths" in lowered, "Contract must forbid absolute paths in names"


def test_full_total_computed_and_pilot_counts() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    actual = _collected_counts()
    assert actual == EXPECTED_COUNTS, (
        f"Pinned pilot counts drifted from collected reality: {actual}"
    )
    assert sum(actual.values()) == EXPECTED_TOTAL, "Pilot total must be 224"
    documented = {key: _documented_count(doc, key) for key in EXPECTED_KEYS}
    assert documented == actual, (
        f"Documented pilot counts must match collected pytest counts: {documented} != {actual}"
    )
    assert re.search(r"(?:total|full[- ]pass|max[- ]score)[^\n]*\b224\b", lowered), (
        "Contract must record the 224-case Selection pilot total"
    )
    for key in actual:
        assert key in doc, f"Contract must list pilot exercise key {key}"
    assert "computed" in lowered and "sum" in lowered, (
        "Contract must state the full-pass total is computed as the sum (not hardcoded)"
    )


def test_pilot_titles_match_exercise_json() -> None:
    doc = _read_doc()
    actual_titles = _exercise_titles()
    assert actual_titles == EXPECTED_TITLES, (
        f"Pinned pilot titles drifted from exercise.json: {actual_titles}"
    )
    for key, title in actual_titles.items():
        assert title in doc, f"Contract must record the exercise.json title for {key}: {title!r}"


def test_graded_forces_student_variant_solution_reserved_dry_run() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    assert "pytutor_active_variant=student" in lowered, (
        "Contract must state the graded run forces PYTUTOR_ACTIVE_VARIANT=student"
    )
    assert "student variant" in lowered, "Contract must name the graded student variant"
    assert "solution" in lowered and "dry run" in lowered, (
        "Contract must reserve the solution variant for the dry run"
    )


def test_slug_is_operator_input_not_stored() -> None:
    doc = _normalised(_read_doc())
    assert "slug" in doc, "Contract must cover the assignment slug"
    assert "operator input" in doc, "Contract must state the slug is operator input"
    assert "not stored" in doc, "Contract must state the slug is not stored"


def test_selection_is_fixture_not_special_grader() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    assert "selection" in lowered, "Contract must identify the Selection pilot"
    assert "validation fixture" in lowered, (
        "Contract must identify Selection as a validation fixture"
    )
    assert "builder configuration" in lowered or "builder config" in lowered, (
        "Contract must identify Selection as a builder configuration"
    )
    assert re.search(
        r"selection[^.?!\n]{0,120}\bnot\b[^.?!\n]{0,60}special grader",
        lowered,
    ), "Contract must explicitly state that Selection is not a special grader"


def test_no_order_of_teaching_change() -> None:
    lowered = _normalised(_read_doc())
    assert re.search(
        r"no (?:`?orderofteaching(?:\.md)?`? change|"
        r"change to `?orderofteaching(?:\.md)?`?)",
        lowered,
    ), "Contract must explicitly state that there is no OrderOfTeaching change"


# ---------------------------------------------------------------------------
# Classroom 50 mode: the no-argument invocation
# ---------------------------------------------------------------------------


def test_classroom50_mode_is_documented_as_a_no_argument_invocation() -> None:
    """The guide must describe the argument-free run Classroom 50 performs."""
    doc = _read_doc()
    assert _mentions(doc, "no arguments", "no argument", "no-argument", "without arguments"), (
        "Guide must state that Classroom 50 invokes the grader with no arguments"
    )
    assert _mentions(doc, "working directory", "cwd"), (
        "Guide must state where a no-argument run is started"
    )
    assert _near(doc, "working directory", "student checkout", "student root"), (
        "Guide must state that the working directory of a no-argument run is the student checkout"
    )


@pytest.mark.parametrize("variable", RUNNER_IDENTITY_VARIABLES)
def test_classroom50_mode_documents_the_runner_identity_variable(variable: str) -> None:
    """Each identity field of the result is read from a named runner variable."""
    assert variable in _read_doc(), (
        f"Guide must name the {variable} runner variable used for the result identity"
    )


def test_classroom50_mode_documents_the_identity_fallbacks() -> None:
    """OWNER falls back to USERNAME and an absent REVIEW_URL falls back to COMMIT_URL."""
    doc = _read_doc()
    assert "USERNAME" in doc, "Guide must name USERNAME as the OWNER fallback"
    assert _near(doc, "OWNER", "USERNAME"), "Guide must state that OWNER falls back to USERNAME"
    assert _near(doc, "REVIEW_URL", "COMMIT_URL"), (
        "Guide must state that REVIEW_URL falls back to COMMIT_URL"
    )


def test_classroom50_mode_documents_the_supported_assignment_types() -> None:
    """individual, group, and team are accepted; anything else is a grading failure."""
    doc = _normalised(_read_doc())
    assert "assignment_type" in doc, "Guide must document the ASSIGNMENT_TYPE identity field"
    missing = [name for name in SUPPORTED_ASSIGNMENT_TYPES if name not in doc]
    assert not missing, f"Guide must name the supported assignment types, missing {missing}"


def test_classroom50_mode_documents_the_result_path_in_the_student_checkout() -> None:
    """The argument-free run writes the checkout-local ./result.json, not a caller path."""
    doc = _read_doc()
    assert "result.json" in doc, "Guide must name the result document"
    assert _near(
        doc,
        "result.json",
        "working directory",
        "student checkout",
        "current directory",
    ), "Guide must tie result.json to the working directory of the no-argument run"


def test_classroom50_mode_documents_the_dependency_install_before_grading() -> None:
    """The grading interpreter is bootstrapped with pip before pytest is imported."""
    doc = _read_doc()
    assert _mentions(doc, "pip"), "Guide must name pip as the dependency install mechanism"
    assert _near(
        doc,
        "install",
        "classroom 50",
        "no arguments",
        "no-argument",
        "grading interpreter",
    ), "Guide must state that Classroom 50 mode installs the grading dependencies"


# ---------------------------------------------------------------------------
# Local dry run: the explicit option pair
# ---------------------------------------------------------------------------


def test_local_dry_run_options_are_documented_as_a_required_pair() -> None:
    """The grader requires the two local options together; one alone is a usage error."""
    doc = _read_doc()
    for option in LOCAL_MODE_OPTIONS:
        assert option in doc, f"Guide must document the local dry-run option {option}"
    assert _mentions(doc, *_LOCAL_PAIR_PHRASES), (
        f"Guide must state that {' and '.join(LOCAL_MODE_OPTIONS)} are required together"
    )
    assert any(pattern.search(doc) for pattern in _SINGLE_OPTION_ERROR_RES), (
        "Guide must state that supplying only one of the local options is a usage error"
    )


def test_local_dry_run_documents_the_exact_local_identity_values() -> None:
    """A local result carries the documented, non-uploadable identity values."""
    doc = _read_doc()
    assert "submit/local" in doc, "Guide must record the local submission value `submit/local`"
    assert _mentions(doc, "local://"), (
        "Guide must record the local:// commit, release, and review values"
    )
    assert _mentions(doc, *_NON_UPLOADABLE_PHRASES), (
        "Guide must mark the local dry-run identity as non-uploadable"
    )


def test_local_dry_run_does_not_install_dependencies() -> None:
    """The local run uses the developer's environment and installs nothing."""
    doc = _read_doc()
    assert _near(doc, "dry run", "install", "pip"), (
        "Guide must tie the dependency install discussion to the dry run"
    )
    assert _mentions(doc, *_NO_LOCAL_INSTALL_PHRASES), (
        "Guide must state that the local dry run installs nothing"
    )


# ---------------------------------------------------------------------------
# Result document: canonical field names
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ("schema", "test-name", "passed"))
def test_result_document_documents_the_canonical_field_name(field: str) -> None:
    """The guide must present each canonical field as a key of the result document.

    The field must appear as a key, i.e. in a code span or in quotes, so prose
    that merely contains the same word cannot pass for the contract.
    """
    assert _documents_result_field(_read_doc(), field), (
        f"Guide must document `{field}` as a key of the result document"
    )


def test_result_document_documents_the_totals_as_sums_over_the_case_rows() -> None:
    """`score` and `max-score` total the case rows, one point per passing case.

    The guide already records the Selection pilot's collected-case totals, so a
    bare mention of "max-score" is not enough: the totals must be tied to the
    per-case rows of a result document.
    """
    doc = _read_doc()
    for field in ("score", "max-score"):
        assert _documents_result_field(doc, field), (
            f"Guide must document `{field}` as a key of the result document"
        )
    totals_contexts = _contexts_of(doc, "`max-score`") + _contexts_of(doc, "max-score")
    assert any(_mentions(context, *_DERIVATION_PHRASES) for context in totals_contexts), (
        "Guide must state that the result totals are sums, totals, or aggregates of the rows"
    )
    assert any(_mentions(context, *_ROW_PHRASES) for context in totals_contexts), (
        "Guide must tie the result totals to the per-case rows, not only to pilot counts"
    )


# ---------------------------------------------------------------------------
# Deployment: build, place at the assignment directory, commit
# ---------------------------------------------------------------------------


def test_deployment_workflow_documents_the_build_place_commit_sequence() -> None:
    """The built bundle is placed at the assignment directory and committed."""
    doc = _read_doc()
    assert BUNDLE_DESTINATION in doc, (
        f"Guide must document the bundle destination {BUNDLE_DESTINATION}"
    )
    assert _near(doc, BUNDLE_DESTINATION, "commit"), (
        f"Guide must state that the bundle placed at {BUNDLE_DESTINATION} is committed"
    )
    assert _near(doc, "build", "autograders/"), (
        "Guide must present building the bundle as the step before placing it"
    )


def test_assignment_keeps_the_default_autograder() -> None:
    """The bundle is a per-assignment autograder override, so the assignment is unchanged."""
    doc = _read_doc()
    assert _mentions(
        doc, 'autograder: "default"', "autograder: `default`", "autograder: default"
    ), 'Guide must state that the assignment keeps `autograder: "default"`'


# ---------------------------------------------------------------------------
# Stale wording, withdrawn features, and link/reference validation
# ---------------------------------------------------------------------------


def test_withdrawn_requirements_are_absent_from_the_affected_docs() -> None:
    """No directly affected document may describe a requirement SPEC.md withdrew."""
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {term!r}"
        for path in AFFECTED_DOCS
        for term in WITHDRAWN_TERMS
        if term in _normalised(_read(path))
    ]
    assert not offenders, f"withdrawn requirements must not be documented: {offenders}"


def test_superseded_result_fields_are_not_presented_in_the_affected_docs() -> None:
    """`version` and `name` may only appear where a document says they are gone."""
    offenders: list[str] = []
    for path in AFFECTED_DOCS:
        text = _read(path)
        for field in _SUPERSEDED_RESULT_FIELDS:
            pattern = _QUOTED_FIELD_TEMPLATE.format(field=field)
            for match in re.finditer(pattern, text):
                window = text[max(0, match.start() - 160) : match.end() + 160]
                if not any(marker in _normalised(window) for marker in _REMOVAL_MARKERS):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: `{field}`")
    assert not offenders, f"superseded result fields must not be described: {offenders}"


def test_affected_doc_links_resolve_to_existing_files() -> None:
    """Every relative markdown link in a directly affected document resolves."""
    missing = [
        f"{path.relative_to(REPO_ROOT)} -> {target}"
        for path in AFFECTED_DOCS
        for target in _MARKDOWN_LINK_RE.findall(_read(path))
        if "://" not in target and not (path.parent / target.split("#", 1)[0]).exists()
    ]
    assert not missing, f"documentation links must resolve: {missing}"


@pytest.mark.parametrize("entry_point", DOCUMENTED_ENTRY_POINTS)
def test_documented_cli_entry_points_exist(entry_point: str) -> None:
    """The commands the guide teaches must point at scripts that really exist."""
    assert entry_point in _read_doc(), f"Guide must document the {entry_point} command"
    assert (REPO_ROOT / entry_point).is_file(), f"{entry_point} does not exist"
