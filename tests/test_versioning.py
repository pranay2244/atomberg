"""Tests that keep Home Assistant and release version metadata consistent."""

import json
import re
import unittest
from pathlib import Path

from custom_components.atomberg_independent.const import INTEGRATION_VERSION


ROOT = Path(__file__).resolve().parents[1]


class VersionMetadataTests(unittest.TestCase):
    def test_manifest_and_diagnostics_release_versions_match(self) -> None:
        manifest_path = (
            ROOT / "custom_components" / "atomberg_independent" / "manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], INTEGRATION_VERSION)

    def test_release_version_is_semantic_version(self) -> None:
        self.assertRegex(
            INTEGRATION_VERSION,
            re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"),
        )


if __name__ == "__main__":
    unittest.main()
