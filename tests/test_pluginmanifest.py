"""Structural checks on the Claude Code plugin manifests.

These guard the fields whose absence breaks installation silently: a user runs
`/plugin marketplace add` and it fails, with nothing in CI to have warned us.
`claude plugin validate --strict` covers the same ground but needs the Claude
CLI in the pipeline; this keeps the check self-owned and dependency-free.

Judgment calls about skill *content* (does the description state when to use
the skill rather than summarising its workflow?) stay with human review.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO_ROOT: Path = Path(__file__).parent.parent
MARKETPLACE_PATH: Path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SEMVER: re.Pattern[str] = re.compile(r"^\d+\.\d+\.\d+$")


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


@pytest.fixture
def marketplace() -> Dict[str, Any]:
    return _load(MARKETPLACE_PATH)


@pytest.fixture
def plugin_entries(marketplace: Dict[str, Any]) -> List[Dict[str, Any]]:
    return marketplace["plugins"]


def test_marketplace_manifest_is_valid_json() -> None:
    assert MARKETPLACE_PATH.exists(), f"missing {MARKETPLACE_PATH}"
    _load(MARKETPLACE_PATH)


def test_marketplace_declares_every_field_the_installer_shows(
    marketplace: Dict[str, Any],
) -> None:
    for field in ("name", "description", "owner", "plugins"):
        assert marketplace.get(field), f"marketplace.json is missing '{field}'"
    assert marketplace["owner"].get("name"), "marketplace owner needs a name"


def test_marketplace_lists_at_least_one_plugin(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    assert plugin_entries, "marketplace.json lists no plugins"


def test_each_plugin_entry_is_complete(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    for entry in plugin_entries:
        for field in ("name", "source", "description"):
            assert entry.get(field), f"plugin entry {entry!r} is missing '{field}'"


def test_each_plugin_source_resolves_to_a_real_manifest(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    for entry in plugin_entries:
        manifest = REPO_ROOT / entry["source"] / ".claude-plugin" / "plugin.json"
        assert manifest.exists(), (
            f"marketplace points at {entry['source']}, but {manifest} does not exist"
        )


def test_plugin_manifest_name_matches_its_marketplace_entry(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    """A mismatch breaks `/plugin install <name>@<marketplace>` with no other signal."""
    for entry in plugin_entries:
        manifest = _load(REPO_ROOT / entry["source"] / ".claude-plugin" / "plugin.json")
        assert manifest["name"] == entry["name"], (
            f"marketplace calls it {entry['name']!r}, "
            f"plugin.json calls it {manifest['name']!r}"
        )


def test_plugin_manifest_is_complete_and_versioned(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    for entry in plugin_entries:
        manifest = _load(REPO_ROOT / entry["source"] / ".claude-plugin" / "plugin.json")
        for field in ("name", "version", "description"):
            assert manifest.get(field), f"{entry['name']}: plugin.json needs '{field}'"
        assert SEMVER.match(manifest["version"]), (
            f"{entry['name']}: version {manifest['version']!r} is not X.Y.Z — "
            "users only receive updates when this is bumped"
        )


def test_marketplace_and_plugin_descriptions_are_not_the_same_string(
    marketplace: Dict[str, Any], plugin_entries: List[Dict[str, Any]]
) -> None:
    """They appear side by side in the installer and describe different things."""
    marketplace_description = marketplace.get("description")
    if not marketplace_description:
        pytest.skip("no marketplace description — covered by the completeness test")
    for entry in plugin_entries:
        assert marketplace_description != entry["description"], (
            f"{entry['name']}: marketplace and plugin descriptions are identical"
        )


def test_every_shipped_skill_has_name_and_description_frontmatter(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    """A skill without a description is never surfaced to an agent."""
    for entry in plugin_entries:
        skills_dir = REPO_ROOT / entry["source"] / "skills"
        if not skills_dir.exists():
            continue
        for skill_file in skills_dir.glob("*/SKILL.md"):
            text = skill_file.read_text()
            assert text.startswith("---\n"), f"{skill_file} has no YAML frontmatter"
            frontmatter = text.split("---\n", 2)[1]
            for field in ("name:", "description:"):
                assert field in frontmatter, f"{skill_file} frontmatter needs '{field}'"


def test_skill_reference_links_point_at_files_that_exist(
    plugin_entries: List[Dict[str, Any]],
) -> None:
    """A dead `reference/*.md` pointer sends an agent looking for nothing."""
    for entry in plugin_entries:
        skills_dir = REPO_ROOT / entry["source"] / "skills"
        if not skills_dir.exists():
            continue
        for skill_file in skills_dir.glob("*/SKILL.md"):
            referenced = re.findall(
                r"`(reference/[\w./-]+\.md)`", skill_file.read_text()
            )
            for target in referenced:
                assert (skill_file.parent / target).exists(), (
                    f"{skill_file} points at {target}, which does not exist"
                )
