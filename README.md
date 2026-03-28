# GEOS Field Dictionary

The GEOS Field Dictionary (`geos_field_dictionary.yaml`) is the authoritative registry of standard field names used across GEOS Earth System Model components. It provides standardized metadata for each field to support consistent NetCDF output, unit checking, and regridding decisions in [MAPL](https://github.com/GEOS-ESM/MAPL).

## Current Schema Version

**v0.2.0** — See [CHANGELOG.md](CHANGELOG.md) for migration notes from v0.1.x.

The schema RFC is documented in [`docs/schema-rfc-v0.2.0.md`](docs/schema-rfc-v0.2.0.md).

---

## Schema Reference

Each entry in `geos_field_dictionary.yaml` is keyed by the field's **standard name** (following CF Conventions where possible, using snake_case). The dictionary is wrapped in a top-level `field_dictionary` object:

```yaml
field_dictionary:
  version: 0.2.0
  metadata:
    last_modified: 2026-03-23T00:00:00Z
    institution: NASA GMAO
    contact: mapl-support@lists.nasa.gov
    description: GEOS field dictionary

  entries:
    field_name:
      long_name: ...
      canonical_units: ...
      verification_status: ...
      conserved: ...
```

### Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `long_name` | string | **Yes** | auto-generated¹ | Human-readable description for NetCDF output |
| `canonical_units` | string | **Yes** | `"1"` | Authoritative units string (UDUNITS-2 compatible) |
| `verification_status` | enum | **Yes** | `unverified` | Quality level: `unverified`, `verified`, or `cf_compliant` |
| `conserved` | boolean | **Yes** | `false` | Whether this field is a conserved quantity (drives regrid method selection) |
| `aliases` | list of string | No | `[]` | Short names used in code (formerly `short_names`) |
| `physical_dimension` | string | No | *(omitted)* | Physical category from the controlled vocabulary |
| `provenance` | object | No | *(omitted)* | Verification provenance |
| `provenance.verified_by` | string | No | *(omitted)* | Name of scientist who verified the entry |
| `components` | list of string | No | `[]` | GEOS components that use this field |

¹ During migration from v0.1.x, `long_name` is auto-generated from the standard name (underscores replaced with spaces, title-cased) when a scientist has not yet supplied one.

---

### `long_name`

A human-readable description of the field, used as the `long_name` attribute in NetCDF output by MAPL. Should be a concise phrase in title case.

```yaml
air_temperature:
  long_name: Air Temperature
```

---

### `canonical_units`

The authoritative physical unit for this field, expressed as a [UDUNITS-2](https://www.unidata.ucar.edu/software/udunits/) compatible string. Individual GEOS components may use different internal units, but the dictionary records the canonical reference unit.

```yaml
air_temperature:
  canonical_units: K

specific_humidity:
  canonical_units: kg kg-1

eastward_wind:
  canonical_units: m s-1
```

---

### `verification_status`

Indicates the level of scientific review for this entry. One of three values:

| Value | Meaning |
|---|---|
| `unverified` | Entry exists but has not been scientifically reviewed. Metadata may be auto-generated or placeholder. |
| `verified` | A domain scientist has reviewed and confirmed the `long_name`, `canonical_units`, and other metadata. |
| `cf_compliant` | Entry is consistent with [CF Conventions](https://cfconventions.org/) standard names and has been verified. |

The 43 fields listed in [`cf_compliant_geos_long_names.txt`](cf_compliant_geos_long_names.txt) have `verification_status: cf_compliant`.

```yaml
air_temperature:
  verification_status: cf_compliant

surface_temperature:
  verification_status: verified

10-meter_air_temperature:
  verification_status: unverified
```

---

### `conserved`

A boolean flag indicating whether this field is a conserved quantity. When `true`, MAPL will select a conservative regridding method by default. Most fields are `false`.

Fields that are typically `conserved: true` include:
- Mass fractions (e.g., `mass_fraction_of_cloud_liquid_water_in_air`)
- Mixing ratios

```yaml
mass_fraction_of_cloud_liquid_water_in_air:
  conserved: true

air_temperature:
  conserved: false
```

---

### `aliases`

A list of short names or alternative identifiers used for this field in GEOS component code, MAPL `IMPORT`/`EXPORT` specs, or legacy files. For documentation purposes only — MAPL does not use this field at runtime.

Renamed from `short_names` in v0.1.x.

```yaml
air_temperature:
  aliases: [T, TEMP]

specific_humidity:
  aliases: [Q, QV]
```

---

### `physical_dimension`

An optional category classifying the physical nature of the field. Drawn from a controlled vocabulary (see below). Enables future machine-readable logic such as unit-consistency checks and default regrid-method selection by category.

**Controlled vocabulary** (extensible):

```
temperature        pressure           density
velocity           acceleration       mass
mass_flux          mass_fraction      mole_fraction
energy             energy_flux        power
length             area               volume
concentration      mixing_ratio
frequency          angular_velocity
dimensionless      other
```

```yaml
air_temperature:
  physical_dimension: temperature

eastward_wind:
  physical_dimension: velocity

mass_fraction_of_cloud_liquid_water_in_air:
  physical_dimension: mass_fraction
```

---

### `provenance`

Optional sub-object recording who verified the entry. Populated when `verification_status` is `verified` or `cf_compliant`.

```yaml
surface_temperature:
  verification_status: verified
  provenance:
    verified_by: Jane Doe
```

---

### `components`

A list of GEOS component names that use this field. Useful for understanding the impact of renaming or removing a field. Not used by MAPL at runtime.

```yaml
air_temperature:
  components: [MOIST, PHYSICS, CHEMISTRY]
```

---

## Complete Examples

### CF-compliant, fully verified entry

```yaml
air_temperature:
  long_name: Air Temperature
  canonical_units: K
  verification_status: cf_compliant
  conserved: false
  physical_dimension: temperature
  aliases: [T, TEMP]
  components: [MOIST, PHYSICS]
```

### Verified GEOS-specific entry

```yaml
surface_temperature:
  long_name: Surface Skin Temperature
  canonical_units: K
  verification_status: verified
  conserved: false
  physical_dimension: temperature
  provenance:
    verified_by: Jane Doe
  aliases: [TS]
  components: [SURFACE, MOIST]
```

### Migrated (unverified) entry with minimal fields

```yaml
10-meter_air_temperature:
  long_name: 10-Meter Air Temperature
  canonical_units: K
  verification_status: unverified
  conserved: false
  aliases: [T10M]
  components: [SURFACE]
```

### Conserved quantity — drives conservative regridding

```yaml
mass_fraction_of_cloud_liquid_water_in_air:
  long_name: Mass Fraction of Cloud Liquid Water in Air
  canonical_units: kg kg-1
  verification_status: cf_compliant
  conserved: true
  physical_dimension: mass_fraction
  aliases: [QL]
  components: [MOIST]
```

---

## Validation

A schema validation tool is provided at [`utils/validate_schema.py`](utils/validate_schema.py). It checks:

- All required fields are present (`long_name`, `canonical_units`, `verification_status`, `conserved`)
- `verification_status` is one of the three allowed enum values
- `canonical_units` is a non-empty string
- `physical_dimension`, if present, is from the controlled vocabulary
- `conserved` is a boolean
- No duplicate standard names (the YAML parser catches these, but the validator double-checks)

### Running the validator

```bash
python utils/validate_schema.py geos_field_dictionary.yaml
```

The validator exits with code `0` on success or `1` if errors are found.

CI runs the validator automatically on every pull request via [`.github/workflows/validate-schema.yml`](.github/workflows/validate-schema.yml).

---

## Migration from v0.1.x

If you have a v0.1.x format dictionary (flat YAML, using `units`, `short_names`, and `incomplete`), a migration script is provided in `utils/migrate_to_v0.2.0.py` (created in Phase 4).

Summary of field renames:

| v0.1.x | v0.2.0 | Notes |
|---|---|---|
| `short_names` | `aliases` | Renamed |
| `units` | `canonical_units` | Renamed |
| `incomplete: true` | `verification_status: unverified` | Replaced with enum |
| *(absent)* | `long_name` | New required field |
| *(absent)* | `conserved` | New required field (default `false`) |
| *(absent)* | `physical_dimension` | New optional field |
| *(absent)* | `provenance` | New optional field |
| `components` | `components` | Unchanged, now optional |

See [`docs/schema-rfc-v0.2.0.md`](docs/schema-rfc-v0.2.0.md) for full migration rationale.

---

## Related

- [MAPL](https://github.com/GEOS-ESM/MAPL) — The GEOS model framework that reads this dictionary
- [CF Conventions](https://cfconventions.org/) — Standard names followed where possible
- [UDUNITS-2](https://www.unidata.ucar.edu/software/udunits/) — Unit string format used by `canonical_units`
- MAPL Epic: [GEOS-ESM/MAPL#4438](https://github.com/GEOS-ESM/MAPL/issues/4438)
