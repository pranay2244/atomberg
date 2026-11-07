# Versioning and Home Assistant upgrades

The integration has two independent version numbers:

1. **Release version** (`custom_components/atomberg_independent/manifest.json`,
   mirrored by `INTEGRATION_VERSION` in `const.py`). This is the user-facing
   integration release version used by HACS and shown in config-entry
   diagnostics. Follow semantic versioning: patch for fixes, minor for
   compatible features, and major for breaking user-facing changes. Keep both
   values identical; `tests/test_versioning.py` checks this.
2. **Config-entry schema version** (`VERSION` and `MINOR_VERSION` on
   `ConfigFlow`). Change these only when the shape or meaning of saved config
   entry data/options changes, not for every code release. Increment the minor
   version for a backwards-compatible schema change, or the major version for
   an incompatible one. Implement and test `async_migrate_entry` before
   releasing a schema change. Never discard unknown saved fields during a
   migration.

## Publishing a release

1. Update `manifest.json` and `INTEGRATION_VERSION` together.
2. Run `python3 -m unittest discover -s tests -v`.
3. Run the Home Assistant `hassfest` and HACS integration validation checks,
   then commit the change and push it to `main`.
4. Before claiming support for a hardware-dependent feature, validate its
   protocol mapping against controlled physical-device observations. Keep
   unverified controls hidden by default and document the limitation.
5. Create a Git tag named `v<manifest-version>` (for example, `v0.4.8`) and a
   stable GitHub release for that tag. Do not mark normal releases as
   pre-releases. HACS can then offer the tagged release.
6. In Home Assistant, update the custom integration through HACS and restart
   Home Assistant.

Home Assistant device `sw_version` is reserved for a device firmware version
that has actually been observed. It must not be filled with the integration
release version or an inferred value.
