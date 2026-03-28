# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`long_name`** (required): Human-readable field description used as the NetCDF `long_name` attribute by MAPL. During migration, values are auto-generated from the standard name (underscores replaced with spaces, title-cased). Scientists should replace auto-generated values with accurate descriptions as part of the verification workflow.

- **`conserved`** (required, default `false`): Boolean flag indicating whether the field is a conserved quantity. When `true`, MAPL selects a conservative regridding method by default. Set to `true` during migration for 149 entries matched by name (mass fractions, mixing ratios, specific humidity) or unit (`kg kg-1`).

- **`verification_status`** (required, default `unverified`): Three-level enum replacing the former `incomplete` boolean. Allowed values:
  - `unverified` — entry has not been scientifically reviewed (assigned to all migrated entries)
  - `verified` — a domain scientist has reviewed `long_name`, `canonical_units`, and other metadata
  - `cf_compliant` — entry is consistent with CF Conventions standard names (assigned to the 43 fields in `cf_compliant_geos_long_names.txt`)

- **`physical_dimension`** (optional): Classifies the field by physical category using a controlled vocabulary (`temperature`, `pressure`, `velocity`, `mass_fraction`, etc.). Inferred automatically from `canonical_units` during migration for 1,798 of 2,359 entries; the remaining 561 are left blank for manual review. Enables future unit-consistency checks and regrid-method inference.

- **`provenance`** (optional): Sub-object recording who verified an entry. Contains `verified_by` (string, name of scientist). Populated when `verification_status` is `verified` or `cf_compliant`.

- **Top-level `field_dictionary` wrapper**: The YAML file now has a top-level `field_dictionary` key containing `version`, `metadata`, and `entries` sub-keys. The `version` field allows MAPL to detect old-format files and emit appropriate warnings.

- `docs/schema-rfc-v0.2.0.md`: Full schema RFC with motivation, open questions, proposed schema, migration strategy, and MAPL impact analysis.

- `utils/validate_schema.py`: Schema validation tool. Checks required fields, enum values, unit string presence, controlled vocabulary for `physical_dimension`, and boolean types. Exits with code 1 on error. Run via `uv run utils/validate_schema.py geos_field_dictionary.yaml`. Pass `--strict` to enforce v0.2.0 structure (CI now uses `--strict`).

- `utils/migrate_to_v0.2.0.py`: Migration script that converts a v0.1.x flat dictionary to v0.2.0 format. Auto-generates `long_name`, infers `physical_dimension` from units, sets `conserved` for known mass-fraction/mixing-ratio fields, and marks CF-compliant entries. Run via `uv run utils/migrate_to_v0.2.0.py`.

- `README.md`: Comprehensive schema reference documentation covering all fields, controlled vocabulary, complete examples for each verification status level, migration table, and validator usage.

- `.github/workflows/validate-schema.yml`: CI workflow that runs `utils/validate_schema.py --strict` on every pull request touching the dictionary or validator, preventing schema-invalid entries from being merged.

- `CONTRIBUTING.md`: Field verification workflow guide for domain scientists.

- `.github/ISSUE_TEMPLATE/field-verification.md`: Issue template for per-field verification tracking.

### Changed

- **`short_names` → `aliases`**: The `short_names` list field has been renamed to `aliases` for consistency with CF Conventions and NUOPC terminology. Existing values are preserved; only the key name changes.

- **`units` → `canonical_units`**: The `units` field has been renamed to `canonical_units` to make explicit that this is the authoritative reference unit for the field. Individual GEOS components may use different internal units, but the dictionary always records the canonical form.

- **`components`** is now optional: Previously implied as required; now explicitly documented as optional. Existing values are preserved. New entries do not need to populate this field.

- **`geos_field_dictionary.yaml`**: All 2,359 entries migrated to v0.2.0 format (43 `cf_compliant`, 149 `conserved: true`, 1,798 with `physical_dimension` inferred).

### Removed

- **`incomplete`**: The `incomplete: true` boolean has been removed and replaced by `verification_status: unverified`. Since all ~2,360 existing entries had `incomplete: true`, there is no information loss.

### Migration Notes (v0.1.x → v0.2.0)

`utils/migrate_to_v0.2.0.py` was run against all 2,359 entries and applies the following transformations:

| v0.1.x | v0.2.0 | Action |
|---|---|---|
| `short_names: [...]` | `aliases: [...]` | Key renamed; values preserved |
| `units: X` | `canonical_units: X` | Key renamed; values preserved |
| `incomplete: true` | `verification_status: unverified` | Replaced with enum |
| *(absent)* | `long_name: <auto>` | Auto-generated from standard name (underscores→spaces, title case) |
| *(absent)* | `conserved: true/false` | Inferred from name and units patterns; 149 entries set `true` |
| *(absent)* | `physical_dimension: <inferred>` | Inferred from `canonical_units` for 1,798 entries; 561 left blank |
| `components: [...]` | `components: [...]` | Unchanged |

The 43 fields in `cf_compliant_geos_long_names.txt` are set to `verification_status: cf_compliant`; all others are `unverified`.

### Breaking Changes

- MAPL v3+ reads `canonical_units` (not `units`). Old-format dictionaries (v0.1.x) are supported in PERMISSIVE mode; STRICT mode requires v0.2.0+.
- The top-level structure changes from a flat mapping to `field_dictionary.entries`. Tooling that reads the YAML directly must be updated.

---

## [0.1.0] - Prior to 2026

Initial schema with four fields per entry: `components`, `incomplete`, `short_names`, `units`.

