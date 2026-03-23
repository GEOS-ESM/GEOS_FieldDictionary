# Schema RFC: GEOS Field Dictionary v0.2.0

**Date:** 2026-03-23  
**Status:** Proposed — Awaiting Team Review  
**Related Issues:**
- GEOS_FieldDictionary: [#1](https://github.com/GEOS-ESM/GEOS_FieldDictionary/issues/1), [#2](https://github.com/GEOS-ESM/GEOS_FieldDictionary/issues/2), [#3](https://github.com/GEOS-ESM/GEOS_FieldDictionary/issues/3)
- MAPL Epic: [#4438](https://github.com/GEOS-ESM/MAPL/issues/4438)

---

## 1. Motivation

The current `geos_field_dictionary.yaml` schema (v0.1.x) contains ~2,360 entries with four fields each:

```yaml
field_name:
  components: [LIST]   # Which GEOS components use this field
  incomplete: true     # Whether metadata is complete
  short_names: [LIST]  # Abbreviated names used in code
  units: str           # Physical units
```

This schema was a useful starting point but has several gaps that limit its usefulness in MAPL3:

1. **No `long_name`** — MAPL components need a human-readable description for NetCDF output.
2. **`incomplete: true` everywhere** — The flag is semantically unclear and 100% of entries have the same value, making it meaningless.
3. **No verification status** — Cannot distinguish entries that have been scientifically reviewed from placeholders.
4. **No conserved-quantity flag** — Cannot drive default regrid method selection.
5. **No physical dimension** — Cannot support regrid-method or unit-check logic.
6. **`short_names` naming** — Inconsistent with downstream usage; `aliases` is a clearer term.

This RFC proposes v0.2.0 of the schema to address these gaps while remaining backward compatible.

---

## 2. Open Questions for Team Review

The following five questions need team consensus before implementation begins. Recommended answers are provided and justified, but the team should validate them.

### Q1: Field naming — `units` → `canonical_units` and `short_names` → `aliases`?

**Options:**

| Option | Keep existing | Rename both | Rename only `short_names` |
|--------|--------------|-------------|--------------------------|
| `units` key | `units` | `canonical_units` | `units` |
| `short_names` key | `short_names` | `aliases` | `aliases` |

**Recommendation:** Rename both.

- `canonical_units`: Makes explicit that this is the *authoritative* unit for the field (not whatever units a given component might choose to use). The word "canonical" communicates that overrides are allowed.
- `aliases`: `short_names` is ambiguous — are these short *variable* names (like T, Q) or short *long_names*? `aliases` is the standard term used by CF conventions and NUOPC for alternative names.

**Migration impact:** All 2,360 entries rename two keys. A migration script handles this automatically (see Section 5).

---

### Q2: Keep `incomplete` flag or replace with `verification_status`?

**Options:**

| Option | Description |
|--------|-------------|
| Keep `incomplete` | Boolean flag, currently always `true` |
| Replace with `verification_status` | Three-level enum: `unverified` / `verified` / `cf_compliant` |
| Keep both | Retain `incomplete` for backward compat, add `verification_status` |

**Recommendation:** Replace `incomplete` with `verification_status`.

Rationale:
- `incomplete` is a boolean that collapses "we haven't looked at this" and "this is wrong" into one value. It cannot represent partial verification.
- All 2,360 current entries have `incomplete: true`, so there is no information loss in replacing it.
- A three-level enum allows a migration path: entries start as `unverified`, domain scientists promote them to `verified`, and eventually CF-compliant entries are marked `cf_compliant`.
- The 43 fields in `cf_compliant_geos_long_names.txt` can be immediately set to `verification_status: cf_compliant`.

**Migration:** Set `verification_status: unverified` for all current entries; set `verification_status: cf_compliant` for the 43 known CF-compliant fields.

---

### Q3: Keep `components` field?

**Options:**

| Option | Description |
|--------|-------------|
| Keep | Retain provenance information about which GEOS components use this field |
| Remove | Field is not used by MAPL at runtime; reduces maintenance burden |
| Keep as optional | Keep but do not require for new entries |

**Recommendation:** Keep as optional.

Rationale:
- The `components` field is not used at runtime by MAPL but is useful for human provenance: it answers "which components will break if I rename this field?"
- Removing it would destroy information that was laboriously collected.
- Making it optional reduces friction for adding new entries.

---

### Q4: Physical dimension vocabulary — controlled list or free-form string?

**Options:**

| Option | Description |
|--------|-------------|
| Controlled vocabulary | Enum-like: `temperature`, `pressure`, `velocity`, etc. |
| Free-form string | Any string allowed |
| Optional / omitted for now | Leave out of v0.2.0, add in v0.3.0 |

**Recommendation:** Use a controlled vocabulary but treat it as optional in v0.2.0.

Rationale:
- A controlled vocabulary enables machine-readable logic (e.g., selecting regrid method by category, unit consistency checks). Free-form strings do not.
- However, classifying all 2,360 entries in v0.2.0 is a large manual effort that should not block the schema migration.
- Making `physical_dimension` optional allows the migration script to leave it blank initially, while new entries and verified entries add it incrementally.

**Proposed controlled vocabulary** (extensible, not exhaustive):

```
temperature, pressure, density, velocity, acceleration,
mass, mass_flux, mass_fraction, mole_fraction,
energy, energy_flux, power,
length, area, volume,
concentration, mixing_ratio,
frequency, angular_velocity,
dimensionless, other
```

---

### Q5: Default regrid method — per-field flag or category-based?

**Options:**

| Option | Description |
|--------|-------------|
| Per-field `conserved` boolean | Each entry explicitly marks whether it is a conserved quantity |
| Category-based | Infer from `physical_dimension` (e.g., `mass_fraction` → conservative) |
| Both | `conserved` flag with category as fallback |

**Recommendation:** Per-field `conserved` boolean, with category-based inference as a future enhancement.

Rationale:
- A boolean `conserved` flag is simple, explicit, and unambiguous. Scientists can mark specific fields.
- Category-based inference is attractive but fragile: not all mass fractions need conservative regridding, and rules will require exceptions.
- The two approaches are not mutually exclusive. Start with explicit per-field flags in v0.2.0; revisit category inference in v0.3.0 after real-world experience.
- Default: `conserved: false`. Known conserved quantities (mixing ratios, mass fractions) will be set during Phase 4 migration.

---

## 3. Proposed v0.2.0 Schema

### 3.1 Top-Level Structure

```yaml
field_dictionary:
  version: 0.2.0
  metadata:
    last_modified: 2026-03-23T00:00:00Z
    institution: NASA GMAO
    contact: mapl-support@lists.nasa.gov
    description: >
      GEOS field dictionary. Standard names follow CF conventions where
      possible. See cf_compliant_geos_long_names.txt for verified CF entries.

  entries:
    # ... field entries below
```

### 3.2 Entry Schema

```yaml
field_name:                          # Key: CF standard name (snake_case)
  long_name: str                     # REQUIRED: Human-readable description
  canonical_units: str               # REQUIRED: Authoritative units string (UDUNITS-2)
  verification_status: str           # REQUIRED: unverified | verified | cf_compliant
  conserved: bool                    # REQUIRED: Whether field is a conserved quantity
  aliases: [list]                    # OPTIONAL: Short names used in code (was short_names)
  physical_dimension: str            # OPTIONAL: Category from controlled vocabulary
  provenance:                        # OPTIONAL: Who verified this entry
    verified_by: str                 # Name of scientist
  components: [list]                 # OPTIONAL: Which GEOS components use this field
```

### 3.3 Complete Example

```yaml
field_dictionary:
  version: 0.2.0
  metadata:
    last_modified: 2026-03-23T00:00:00Z
    institution: NASA GMAO
    contact: mapl-support@lists.nasa.gov
    description: GEOS field dictionary

  entries:

    # CF-compliant, fully verified entry
    air_temperature:
      long_name: Air Temperature
      canonical_units: K
      verification_status: cf_compliant
      conserved: false
      physical_dimension: temperature
      aliases: [T, TEMP]
      components: [MOIST, PHYSICS]

    # Verified GEOS-specific entry
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

    # Migrated (unverified) entry with minimal new fields
    10-meter_air_temperature:
      long_name: 10-meter Air Temperature
      canonical_units: K
      verification_status: unverified
      conserved: false
      aliases: [T10M]
      components: [SURFACE]

    # Conserved quantity — drives conservative regrid method
    mass_fraction_of_cloud_liquid_water_in_air:
      long_name: Mass Fraction of Cloud Liquid Water in Air
      canonical_units: kg kg-1
      verification_status: cf_compliant
      conserved: true
      physical_dimension: mass_fraction
      aliases: [QL]
      components: [MOIST]
```

### 3.4 Field Definitions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `long_name` | string | Yes | auto-generated¹ | Human-readable description for NetCDF output |
| `canonical_units` | string | Yes | `"1"` | UDUNITS-2 compatible unit string |
| `verification_status` | enum | Yes | `unverified` | `unverified` / `verified` / `cf_compliant` |
| `conserved` | boolean | Yes | `false` | Whether to use conservative regridding by default |
| `aliases` | list of string | No | `[]` | Alternative short names (documentation only) |
| `physical_dimension` | string | No | `null` | Category from controlled vocabulary |
| `provenance` | object | No | `null` | Verification provenance |
| `provenance.verified_by` | string | No | `null` | Name of scientist who verified entry |
| `components` | list of string | No | `[]` | GEOS components that use this field |

¹ For migration: `long_name` is auto-generated from the standard name (underscores → spaces, title case) if not provided by a scientist.

### 3.5 Verification Status Values

| Value | Meaning |
|-------|---------|
| `unverified` | Entry exists but has not been scientifically reviewed |
| `verified` | A domain scientist has reviewed units and long_name |
| `cf_compliant` | Entry is consistent with CF Conventions standard names |

---

## 4. What Changes in v0.2.0

### Summary of Changes from v0.1.x

| v0.1.x field | v0.2.0 field | Notes |
|-------------|-------------|-------|
| `short_names` | `aliases` | Renamed |
| `units` | `canonical_units` | Renamed |
| `incomplete: true` | `verification_status: unverified` | Replaced |
| *(absent)* | `long_name` | New required field (auto-generated during migration) |
| *(absent)* | `conserved` | New required field (defaults to `false`) |
| *(absent)* | `physical_dimension` | New optional field |
| *(absent)* | `provenance` | New optional field |
| `components` | `components` | Unchanged, now optional |

### What Does NOT Change

- Entry keys (standard names) are unchanged.
- The dictionary is still a flat YAML mapping at the top level (with the addition of the `field_dictionary` wrapper and `entries` sub-key).
- Existing data (`units`, `short_names`, `components`) is preserved, just renamed.
- No entries are removed.

---

## 5. Migration Strategy

### 5.1 Script: `utils/migrate_to_v0.2.0.py`

The migration script (to be created in Phase 4) will:

1. Read all 2,360 entries from the current flat YAML.
2. Wrap them in the `field_dictionary.entries` structure.
3. For each entry:
   - Rename `short_names` → `aliases`
   - Rename `units` → `canonical_units`
   - Remove `incomplete` key
   - Add `verification_status: unverified`
   - Add `conserved: false`
   - Auto-generate `long_name` from standard name (replace `_` with space, title case)
4. For the 43 fields in `cf_compliant_geos_long_names.txt`:
   - Set `verification_status: cf_compliant`
5. Write output to `geos_field_dictionary.yaml`.

### 5.2 Validation

CI will validate the migrated file using `utils/validate_schema.py` (to be created in Phase 1):
- Every entry has `long_name`, `canonical_units`, `verification_status`, `conserved`
- `verification_status` is one of the three allowed values
- `canonical_units` is a non-empty string
- `physical_dimension`, if present, is from the controlled vocabulary

### 5.3 Versioning

- Current dictionary has no version field. v0.2.0 adds `field_dictionary.version`.
- MAPL will check the version field and emit a warning if it encounters an old-format (unversioned) dictionary.
- v0.1.x files remain readable in PERMISSIVE mode; STRICT mode requires v0.2.0+.

---

## 6. Impact on MAPL

This RFC describes the YAML schema only. The Fortran implementation is defined separately in the MAPL integration plan. Key points:

- MAPL reads `canonical_units` (not `units`) from v0.2.0 dictionaries.
- MAPL uses `conserved` to select the default regrid method (conservative vs. bilinear).
- MAPL uses `verification_status` to emit optional warnings.
- MAPL uses `long_name` as the default long_name for NetCDF output.
- MAPL does NOT use `aliases`, `components`, or `provenance` at runtime; these are human-facing only.

---

## 7. Deliverables for Phase 0

- [x] Schema RFC document (this document)
- [ ] Team consensus on the five open questions (Section 2)
- [ ] Migration strategy reviewed (Section 5)
- [ ] Design decisions recorded (update this document with team decisions)

**Gate:** No implementation begins until the team has approved the schema (or documented deviations from the recommendations above).

---

## 8. Discussion Notes

*(To be filled in during/after team review meeting)*

| Question | Decision | Rationale | Date |
|----------|----------|-----------|------|
| Q1: Field naming | | | |
| Q2: `incomplete` vs `verification_status` | | | |
| Q3: Keep `components`? | | | |
| Q4: Physical dimension vocabulary | | | |
| Q5: Default regrid method | | | |

---

*Document prepared by the MAPL Team. Please comment on the linked GitHub issues or in the team review meeting.*
