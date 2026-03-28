# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

### Deprecated

---

## [0.2.0] - Unreleased

### Overview

Schema v0.2.0 introduces new required and optional fields to support MAPL3 integration. All existing entries are migrated with auto-generated values for the new required fields. See [`docs/schema-rfc-v0.2.0.md`](docs/schema-rfc-v0.2.0.md) for full design rationale and team discussion notes.

### Added

- **`long_name`** (required): Human-readable field description used as the NetCDF `long_name` attribute by MAPL. During migration, values are auto-generated from the standard name (underscores replaced with spaces, title-cased). Scientists should replace auto-generated values with accurate descriptions as part of the verification workflow.

- **`conserved`** (required, default `false`): Boolean flag indicating whether the field is a conserved quantity. When `true`, MAPL selects a conservative regridding method by default. Known conserved quantities (mass fractions, mixing ratios) will be identified and set in a subsequent phase.

- **`verification_status`** (required, default `unverified`): Three-level enum replacing the former `incomplete` boolean. Allowed values:
  - `unverified` — entry has not been scientifically reviewed (assigned to all migrated entries)
  - `verified` — a domain scientist has reviewed `long_name`, `canonical_units`, and other metadata
  - `cf_compliant` — entry is consistent with CF Conventions standard names (assigned to the 43 fields in `cf_compliant_geos_long_names.txt`)

- **`physical_dimension`** (optional): Classifies the field by physical category using a controlled vocabulary (`temperature`, `pressure`, `velocity`, `mass_fraction`, etc.). Left blank during migration; populated incrementally as entries are verified. Enables future unit-consistency checks and regrid-method inference.

- **`provenance`** (optional): Sub-object recording who verified an entry. Contains `verified_by` (string, name of scientist). Populated when `verification_status` is `verified` or `cf_compliant`.

- **Top-level `field_dictionary` wrapper**: The YAML file now has a top-level `field_dictionary` key containing `version`, `metadata`, and `entries` sub-keys. The `version` field allows MAPL to detect old-format files and emit appropriate warnings.

- `docs/schema-rfc-v0.2.0.md`: Full schema RFC with motivation, open questions, proposed schema, migration strategy, and MAPL impact analysis.

- `utils/validate_schema.py`: Schema validation tool. Checks required fields, enum values, unit string presence, controlled vocabulary for `physical_dimension`, and boolean types. Exits with code 1 on error. Run via `python utils/validate_schema.py geos_field_dictionary.yaml`.

- `README.md`: Comprehensive schema reference documentation covering all fields, controlled vocabulary, complete examples for each verification status level, migration table, and validator usage.

- `.github/workflows/validate-schema.yml`: CI workflow that runs `utils/validate_schema.py` on every pull request to prevent schema-invalid entries from being merged.

### Changed

- **`short_names` → `aliases`**: The `short_names` list field has been renamed to `aliases` for consistency with CF Conventions and NUOPC terminology. Existing values are preserved; only the key name changes.

- **`units` → `canonical_units`**: The `units` field has been renamed to `canonical_units` to make explicit that this is the authoritative reference unit for the field. Individual GEOS components may use different internal units, but the dictionary always records the canonical form.

- **`components`** is now optional: Previously implied as required; now explicitly documented as optional. Existing values are preserved. New entries do not need to populate this field.

### Removed

- **`incomplete`**: The `incomplete: true` boolean has been removed and replaced by `verification_status: unverified`. Since all ~2,360 existing entries had `incomplete: true`, there is no information loss.

### Migration Notes (v0.1.x → v0.2.0)

A migration script (`utils/migrate_to_v0.2.0.py`, created in Phase 4) automates the following transformations:

| v0.1.x | v0.2.0 | Action |
|---|---|---|
| `short_names: [...]` | `aliases: [...]` | Key renamed; values preserved |
| `units: X` | `canonical_units: X` | Key renamed; values preserved |
| `incomplete: true` | `verification_status: unverified` | Replaced with enum |
| *(absent)* | `long_name: <auto>` | Auto-generated from standard name |
| *(absent)* | `conserved: false` | Set to default |
| `components: [...]` | `components: [...]` | Unchanged |

Additionally, the 43 fields in `cf_compliant_geos_long_names.txt` are set to `verification_status: cf_compliant`.

### Breaking Changes

- MAPL v3+ reads `canonical_units` (not `units`). Old-format dictionaries (v0.1.x) are supported in PERMISSIVE mode; STRICT mode requires v0.2.0+.
- The top-level structure changes from a flat mapping to `field_dictionary.entries`. Tooling that reads the YAML directly must be updated.

---

## [0.1.0] - Prior to 2026

Initial schema with four fields per entry: `components`, `incomplete`, `short_names`, `units`.

