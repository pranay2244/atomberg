"""Tests for the verified model capability registry."""

import unittest

from custom_components.atomberg_independent.models import (
    Capability,
    ModelProfile,
    UNKNOWN_MODEL,
    build_model_registry,
    resolve_model_profile,
)


class ModelRegistryTests(unittest.TestCase):
    def test_empty_registry_does_not_claim_any_model_is_verified(self) -> None:
        self.assertIs(resolve_model_profile("unknown-series"), UNKNOWN_MODEL)

    def test_none_resolves_to_unknown_model(self) -> None:
        self.assertIs(resolve_model_profile(None), UNKNOWN_MODEL)

    def test_explicit_profile_resolves_case_insensitively(self) -> None:
        profile = ModelProfile(
            identifier="sample-1",
            name="Sample Fan",
            capabilities=frozenset({Capability.FAN_POWER}),
            evidence=("test fixture: sample-fan-v1",),
        )
        registry = build_model_registry([profile])

        self.assertIs(resolve_model_profile(" SAMPLE-1 ", registry), profile)

    def test_duplicate_normalized_identifiers_are_rejected(self) -> None:
        first = ModelProfile("sample-1", "First", evidence=("evidence-1",))
        second = ModelProfile("SAMPLE-1", "Second", evidence=("evidence-2",))

        with self.assertRaises(ValueError):
            build_model_registry([first, second])

    def test_profile_requires_evidence(self) -> None:
        with self.assertRaises(ValueError):
            ModelProfile("sample-1", "Sample Fan")


if __name__ == "__main__":
    unittest.main()
