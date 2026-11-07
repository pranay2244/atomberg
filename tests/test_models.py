"""Tests for series-based family hints and capability profiles."""

import unittest

from custom_components.atomberg_independent.models import (
    Capability,
    UNKNOWN_MODEL,
    resolve_model_profile,
)


class ModelRegistryTests(unittest.TestCase):
    def test_unknown_series_does_not_claim_a_retail_model(self) -> None:
        profile = resolve_model_profile("unknown-series")

        self.assertIs(profile, UNKNOWN_MODEL)
        self.assertIn("Unknown", profile.name)

    def test_aris_series_is_reported_as_a_family_hint(self) -> None:
        profile = resolve_model_profile("I3")

        self.assertEqual(profile.name, "Aris family (series hint)")
        self.assertEqual(profile.evidence_status, "unverified")
        self.assertIn(Capability.LIGHT_COLOR_MODE, profile.capabilities)

    def test_i5_is_an_aris_contour_series_hint_not_efficio(self) -> None:
        profile = resolve_model_profile("I5")

        self.assertEqual(profile.name, "Aris Contour family (series hint)")
        self.assertNotIn("Efficio", profile.name)
        self.assertEqual(profile.evidence_status, "unverified")

    def test_efficio_series_name_is_explicitly_a_hint(self) -> None:
        profile = resolve_model_profile("M1")

        self.assertIn("Efficio", profile.name)
        self.assertIn("hint", profile.name)
        self.assertEqual(profile.evidence_status, "unverified")
        self.assertIn(Capability.LIGHT_DISCRETE_INTENSITY, profile.capabilities)
        self.assertNotIn(Capability.LIGHT_BRIGHTNESS, profile.capabilities)

    def test_reference_hardware_test_is_not_attributed_to_this_project(self) -> None:
        self.assertEqual(
            resolve_model_profile("S2").evidence_status,
            "hardware-tested-by-reference-project",
        )
        self.assertEqual(resolve_model_profile("I1").evidence_status, "unverified")

    def test_series_lookup_is_case_insensitive(self) -> None:
        self.assertIs(resolve_model_profile("r1"), resolve_model_profile("R1"))

    def test_unknown_series_does_not_expose_unverified_controls(self) -> None:
        self.assertEqual(resolve_model_profile(None).capabilities, frozenset())


if __name__ == "__main__":
    unittest.main()
