"""Tests that keep Home Assistant and release version metadata consistent."""

import json
import re
import struct
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
        hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "Atomberg")
        self.assertEqual(hacs["name"], manifest["name"])
        self.assertEqual(INTEGRATION_VERSION, "0.4.8")

    def test_brand_icon_sizes_are_square_and_match_home_assistant_assets(self) -> None:
        brand_dir = (
            ROOT
            / "custom_components"
            / "atomberg_independent"
            / "brand"
        )
        for filename, expected_size in (
            ("icon.png", 256),
            ("icon@2x.png", 512),
        ):
            with self.subTest(filename=filename):
                image = (brand_dir / filename).read_bytes()
                self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", image[16:24])
                self.assertEqual((width, height), (expected_size, expected_size))

    def test_release_version_is_semantic_version(self) -> None:
        self.assertRegex(
            INTEGRATION_VERSION,
            re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"),
        )


if __name__ == "__main__":
    unittest.main()
