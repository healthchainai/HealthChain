"""Structural checks for the Codex plugin packaging."""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "plugins/healthchain/.codex-plugin/plugin.json"
MARKETPLACE_PATH = REPO_ROOT / ".agents/plugins/marketplace.json"
SKILL_PATH = REPO_ROOT / "plugins/healthchain/skills/healthchain/SKILL.md"


def test_codex_manifest_is_complete():
    manifest = json.loads(MANIFEST_PATH.read_text())

    assert manifest["name"] == "healthchain"
    assert manifest["version"] == "0.1.0"
    assert manifest["description"]
    assert manifest["author"]["name"]
    assert manifest["skills"] == "./skills/"
    assert manifest["interface"]["displayName"] == "HealthChain"


def test_codex_marketplace_points_at_the_manifest():
    marketplace = json.loads(MARKETPLACE_PATH.read_text())
    entry = next(
        item for item in marketplace["plugins"] if item["name"] == "healthchain"
    )

    assert entry["source"]["path"] == "./plugins/healthchain"
    assert (REPO_ROOT / entry["source"]["path"] / ".codex-plugin/plugin.json").exists()


def test_shared_skill_has_codex_frontmatter_and_references():
    text = SKILL_PATH.read_text()

    assert text.startswith("---\n")
    frontmatter = text.split("---\n", 2)[1]
    assert "name: healthchain" in frontmatter
    assert "description:" in frontmatter
    assert (SKILL_PATH.parent / "reference/api.md").exists()
    assert (SKILL_PATH.parent / "reference/recipes.md").exists()
