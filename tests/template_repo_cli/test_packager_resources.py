"""Tests for copying construct-level additional-resources."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.template_repo_cli.core.packager import TemplatePackager


class TestCopyConstructResources:
    """Tests for copying construct-level additional-resources."""

    def test_copies_additional_resources_folder(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Copy the folder when it exists in the source repo."""
        exercises = ["ex002_sequence_modify_basics"]
        template_packager.copy_construct_resources(temp_dir, exercises)

        resource_dir = temp_dir / "exercises" / "sequence" / "additional-resources"
        assert resource_dir.exists()
        assert resource_dir.is_dir()
        assert (resource_dir / "sequence-cheat-sheet.md").is_file()
        assert (resource_dir / "ARITHMETIC_CHEATSHEET.md").is_file()

    def test_copies_only_once_per_construct(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Multiple exercises from the same construct copy resources only once."""
        exercises = [
            "ex002_sequence_modify_basics",
            "ex003_sequence_modify_variables",
        ]
        template_packager.copy_construct_resources(temp_dir, exercises)

        resource_dir = temp_dir / "exercises" / "sequence" / "additional-resources"
        assert resource_dir.exists()
        assert resource_dir.is_dir()
        assert (resource_dir / "sequence-cheat-sheet.md").is_file()

    def test_does_nothing_for_empty_exercise_list(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Silently do nothing when no exercises are provided."""
        template_packager.copy_construct_resources(temp_dir, [])

        assert not (temp_dir / "exercises").exists()

    def test_skips_construct_without_resources(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Silently skip constructs that do not have an additional-resources folder."""
        # Use a fixture repo with a construct that has no additional-resources
        repo_root = temp_dir / "fixture_repo"
        construct = "selection"
        exercise_key = "ex100_selection_intro"
        exercise_dir = repo_root / "exercises" / construct / exercise_key
        exercise_dir.mkdir(parents=True)
        (exercise_dir / "exercise.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "exercise_key": exercise_key,
                    "exercise_id": 100,
                    "slug": exercise_key,
                    "title": "Selection Intro",
                    "construct": construct,
                    "exercise_type": "modify",
                    "parts": 1,
                }
            ),
            encoding="utf-8",
        )

        packager = TemplatePackager(repo_root)
        packager.copy_construct_resources(temp_dir / "workspace", [exercise_key])

        resource_dir = temp_dir / "workspace" / "exercises" / construct / "additional-resources"
        assert not resource_dir.exists()
