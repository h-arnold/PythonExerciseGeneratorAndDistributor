"""Tests for README generation in the template packager."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from scripts.template_repo_cli.core.packager import TemplatePackager


def _write_missing_title_metadata(path: Path) -> None:
    """Write valid JSON metadata missing required title."""

    path.write_text(
        '{"exercise_key": "ex040_sequence_broken", "construct": "sequence"}\n',
        encoding="utf-8",
    )


def _write_invalid_json_metadata(path: Path) -> None:
    """Write malformed JSON metadata for README failure-path tests."""

    path.write_text("{not-json}\n", encoding="utf-8")


class TestGenerateFiles:
    """Tests for generating template files."""

    @staticmethod
    def _create_readme_contract_repo_fixture(root: Path) -> None:
        """Create a minimal fixture repository tree for README contract tests."""

        template_dir = root / "template_repo_files"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "README.md.template").write_text(
            "# {TEMPLATE_NAME}\n\n## Exercises Included\n\n{EXERCISE_LIST}\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_exercise_metadata(
        root: Path,
        *,
        exercise_key: str,
        construct: str,
        title: str | None,
    ) -> None:
        """Write canonical exercise metadata used by README generation tests."""

        exercise_dir = root / "exercises" / construct / exercise_key
        exercise_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {
            "schema_version": 1,
            "exercise_key": exercise_key,
            "construct": construct,
        }
        if title is not None:
            payload["title"] = title
        (exercise_dir / "exercise.json").write_text(
            json.dumps(payload) + "\n",
            encoding="utf-8",
        )

    def test_generate_readme_groups_numbered_links_by_construct_heading_and_title_text(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """README lists grouped, numbered links by construct with metadata title text."""

        fixture_root = temp_dir / "fixture_repo"
        self._create_readme_contract_repo_fixture(fixture_root)
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex010_control_flow_intro",
            construct="control_flow",
            title="Control Flow Intro",
        )
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex030_control_flow_branching",
            construct="control_flow",
            title="Control Flow Branching",
        )
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex020_sequence_variables",
            construct="sequence",
            title="Sequence Variables",
        )

        template_packager.repo_root = fixture_root
        template_packager.template_files_dir = fixture_root / "template_repo_files"

        template_packager.generate_readme(
            temp_dir,
            "README Contract",
            [
                "ex030_control_flow_branching",
                "ex020_sequence_variables",
                "ex010_control_flow_intro",
            ],
        )

        content_lines = [line.strip() for line in (temp_dir / "README.md").read_text().splitlines()]

        assert any(line == "## Control Flow" for line in content_lines)
        assert any(line == "## Sequence" for line in content_lines)
        assert any(
            line
            == "1. [Control Flow Intro](exercises/control_flow/ex010_control_flow_intro/notebooks/student.ipynb)"
            for line in content_lines
        )
        assert any(
            line
            == "2. [Control Flow Branching](exercises/control_flow/ex030_control_flow_branching/notebooks/student.ipynb)"
            for line in content_lines
        )
        assert any(
            line
            == "1. [Sequence Variables](exercises/sequence/ex020_sequence_variables/notebooks/student.ipynb)"
            for line in content_lines
        )

    def test_generate_readme_sorts_exercise_keys_before_multi_construct_rendering(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """README rendering follows sorted exercise-key ordering with mixed constructs."""

        fixture_root = temp_dir / "fixture_repo"
        self._create_readme_contract_repo_fixture(fixture_root)
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex030_control_flow_branching",
            construct="control_flow",
            title="Control Flow Branching",
        )
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex010_control_flow_intro",
            construct="control_flow",
            title="Control Flow Intro",
        )
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex020_sequence_variables",
            construct="sequence",
            title="Sequence Variables",
        )

        template_packager.repo_root = fixture_root
        template_packager.template_files_dir = fixture_root / "template_repo_files"

        template_packager.generate_readme(
            temp_dir,
            "README Contract",
            [
                "ex030_control_flow_branching",
                "ex020_sequence_variables",
                "ex010_control_flow_intro",
            ],
        )

        content_lines = [line.strip() for line in (temp_dir / "README.md").read_text().splitlines()]
        list_lines = [line for line in content_lines if line.startswith(("1. [", "2. [", "3. ["))]

        assert list_lines == [
            "1. [Control Flow Intro](exercises/control_flow/ex010_control_flow_intro/notebooks/student.ipynb)",
            "2. [Control Flow Branching](exercises/control_flow/ex030_control_flow_branching/notebooks/student.ipynb)",
            "1. [Sequence Variables](exercises/sequence/ex020_sequence_variables/notebooks/student.ipynb)",
        ]

    @pytest.mark.parametrize(
        "broken_metadata_writer",
        [
            pytest.param(
                _write_missing_title_metadata,
                id="missing-title",
            ),
            pytest.param(
                _write_invalid_json_metadata,
                id="invalid-json",
            ),
        ],
    )
    def test_generate_readme_wraps_metadata_errors_with_exercise_key_context_and_cause(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        broken_metadata_writer: Callable[[Path], None],
    ) -> None:
        """README metadata failures are wrapped with exercise-key context and chained cause."""

        fixture_root = temp_dir / "fixture_repo"
        self._create_readme_contract_repo_fixture(fixture_root)
        broken_key = "ex040_sequence_broken"
        broken_metadata_path = (
            fixture_root / "exercises" / "sequence" / broken_key / "exercise.json"
        )
        broken_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        broken_metadata_writer(broken_metadata_path)

        template_packager.repo_root = fixture_root
        template_packager.template_files_dir = fixture_root / "template_repo_files"

        with pytest.raises(ValueError) as exc_info:
            template_packager.generate_readme(temp_dir, "README Contract", [broken_key])

        assert broken_key in str(exc_info.value)
        assert exc_info.value.__cause__ is not None

    def test_generate_readme(self, template_packager: TemplatePackager, temp_dir: Path) -> None:
        """Test creating custom README with exercise list."""
        exercises = ["ex002_sequence_modify_basics", "ex004_sequence_debug_syntax"]

        template_packager.generate_readme(temp_dir, "Test Template", exercises)

        readme = temp_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Test Template" in content
        assert "ex002_sequence_modify_basics" in content

    def test_generate_gitignore(self, template_packager: TemplatePackager, temp_dir: Path) -> None:
        """Test creating appropriate .gitignore."""
        template_packager.copy_template_base_files(temp_dir)

        gitignore = temp_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "__pycache__" in content

    def test_generate_readme_includes_resource_link_when_construct_has_resources(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """README includes an additional-resources link for constructs that have the folder."""
        exercises = ["ex002_sequence_modify_basics", "ex004_sequence_debug_syntax"]
        template_packager.generate_readme(temp_dir, "Test Template", exercises)

        content = (temp_dir / "README.md").read_text()
        assert "Additional Resources" in content
        assert "exercises/sequence/additional-resources/" in content

    def test_generate_readme_omits_resource_link_when_construct_has_no_resources(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """README does not include a resources link when the construct has no additional-resources."""
        # Use a fixture repo where the construct has no additional-resources
        fixture_root = temp_dir / "fixture_repo"
        self._create_readme_contract_repo_fixture(fixture_root)
        self._write_exercise_metadata(
            fixture_root,
            exercise_key="ex010_control_flow_intro",
            construct="control_flow",
            title="Control Flow Intro",
        )

        template_packager.repo_root = fixture_root
        template_packager.template_files_dir = fixture_root / "template_repo_files"

        template_packager.generate_readme(
            temp_dir,
            "No Resources",
            ["ex010_control_flow_intro"],
        )

        content = (temp_dir / "README.md").read_text()
        assert "Additional Resources" not in content
