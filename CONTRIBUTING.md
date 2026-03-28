# Contributing to GEOS Field Dictionary

Thank you for contributing to the GEOS Field Dictionary. This document covers two types of contributions:

1. **Schema/tooling changes** — modifications to `utils/`, `.github/workflows/`, `README.md`, etc.
2. **Field verification** — reviewing and improving entries in `geos_field_dictionary.yaml`

---

## Contributor License Agreement (CLA)

All external developers contributing to GEOS-ESM projects must complete a [Contributor License Agreement](https://github.com/GEOS-ESM/cla).

NOTE: Internal NASA contributors associated with GEOS, including contractors, are covered by other agreements and do not need to sign a CLA.

## License

By contributing to GEOS-ESM projects, you agree your contributions will be licensed under the [Apache 2.0 License](LICENSE).

---

## Schema / Tooling Changes

Open a Pull Request against `main`. CI will automatically run `utils/validate_schema.py --strict geos_field_dictionary.yaml` on any PR that touches the dictionary or the validator. The PR cannot be merged if validation fails.

---

## Field Verification Workflow

The dictionary contains ~2,359 entries. Most are currently `verification_status: unverified` — the metadata was auto-generated during migration and has not been reviewed by a domain scientist. Verification is the primary ongoing contribution activity.

### What needs verifying?

For each entry, a domain scientist should confirm:

| Field | What to check |
|---|---|
| `long_name` | Accurate, human-readable description suitable for NetCDF output |
| `canonical_units` | Correct UDUNITS-2 unit string for this field |
| `physical_dimension` | Appropriate category from the controlled vocabulary (or leave blank if unclear) |
| `conserved` | Should MAPL use conservative regridding for this field by default? |
| `verification_status` | Promote to `verified` (or `cf_compliant` if it matches a CF standard name) |
| `provenance.verified_by` | Add your name |

### Step-by-step guide

1. **Find a field to verify.** Search for `verification_status: unverified` in `geos_field_dictionary.yaml`, or open a [field verification issue](https://github.com/GEOS-ESM/GEOS_FieldDictionary/issues/new?template=field-verification.md) for a specific field.

2. **Check the CF Conventions standard names table** at https://cfconventions.org/standard-names.html. If the field's standard name appears there, the entry should be `cf_compliant`.

3. **Check UDUNITS-2 compatibility** for the `canonical_units` string. Common pitfalls:
   - Use `kg kg-1` not `kg/kg`
   - Use `m s-1` not `m/s`
   - Use `W m-2` not `W/m2`

4. **Edit `geos_field_dictionary.yaml`** to update the entry. Example of a verified entry:

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

5. **Run the validator locally** before opening a PR:

   ```bash
   uv run utils/validate_schema.py --strict geos_field_dictionary.yaml
   ```

6. **Open a Pull Request.** Reference the field verification issue if one exists (e.g., `Closes #42`). The PR description should briefly note what was changed and why.

### Physical dimension vocabulary

Use one of these values for `physical_dimension`:

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

Leave the field blank rather than using `other` if unsure — `other` is a last resort for genuinely unclassifiable fields.

### Conserved quantities

Set `conserved: true` for fields that represent conserved quantities requiring conservative regridding:

- Mass fractions (e.g., `mass_fraction_of_cloud_liquid_water_in_air`)
- Mixing ratios (e.g., `specific_humidity`, moisture tracers)
- Mass-weighted scalar quantities that must be regridded conservatively

Set `conserved: false` for everything else (temperatures, winds, pressures, fluxes, etc.).

### Priority fields

When choosing which fields to verify first, prioritize:

1. Fields used by many components (check the `components` list length)
2. Fields with `verification_status: cf_compliant` — these can often be confirmed quickly against the CF standard names table
3. Core meteorological variables (temperature, humidity, wind, pressure)

---

## Questions?

Open a GitHub issue or contact [mapl-support@lists.nasa.gov](mailto:mapl-support@lists.nasa.gov).
