from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

import ckb


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _project_version() -> str:
    match = re.search(
        r'^version\s*=\s*"([^"]+)"\s*$',
        _read("pyproject.toml"),
        flags=re.MULTILINE,
    )
    if match is None:
        raise AssertionError("pyproject.toml project version is missing")
    return match.group(1)


class ReleaseVersionTests(unittest.TestCase):
    def test_package_and_runtime_versions_match(self) -> None:
        self.assertEqual(ckb.__version__, _project_version())

    def test_current_release_documents_match_project_version(self) -> None:
        version = _project_version()
        changelog_match = re.search(
            r"^## ([0-9]+\.[0-9]+\.[0-9]+)\s*$",
            _read("CHANGELOG.md"),
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(changelog_match)
        self.assertEqual(changelog_match.group(1), version)

        roadmap_match = re.search(
            r"^## 当前基线：v([0-9]+\.[0-9]+\.[0-9]+)\s*$",
            _read("ROADMAP.md"),
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(roadmap_match)
        self.assertEqual(roadmap_match.group(1), version)
        self.assertIn(f"`{version}`：", _read("README.md"))

    def test_versioned_release_snapshot_exists(self) -> None:
        version = _project_version()
        version_token = version.replace(".", "_")
        manifest_path = ROOT / "data" / "releases" / f"v{version_token}.json"
        release_doc = ROOT / "docs" / f"V{version_token}_RELEASE.md"

        self.assertTrue(manifest_path.is_file())
        self.assertTrue(release_doc.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("release_version"), version)
        self.assertEqual(manifest.get("status"), "released")
        self.assertEqual(
            manifest.get("godot_runtime_snapshot", {}).get("bundle_format"),
            "ckb.godot.runtime",
        )
        self.assertEqual(
            manifest.get("engine_validation", {}).get("result"),
            "pass",
        )


if __name__ == "__main__":
    unittest.main()
