# Field Verification Quick-Start Guide

**Audience:** Domain scientists who want to verify GEOS field dictionary entries.  
**Time required:** 5–15 minutes per field.  
**No programming experience required.**

---

## Why verify?

The `geos_field_dictionary.yaml` contains ~2,359 field entries. Most were migrated automatically and are marked `verification_status: unverified`. This means:

- `long_name` was auto-generated (may be imprecise)
- `canonical_units` came from old data (may be wrong)
- `conserved` and `physical_dimension` were inferred (may be incorrect)

Verified entries improve NetCDF output quality, enable correct automatic regridding in MAPL, and build a reliable reference for the whole GEOS team.

---

## Step 1 — Find a field to verify

### Option A: Browse the dictionary directly

Open `geos_field_dictionary.yaml` and search for `verification_status: unverified`. Pick any field you know well.

### Option B: Check the priority list

Run the priority script to see the fields used by the most GEOS components (highest impact first):

```bash
uv run utils/priority_fields.py
```

This prints the top 100 unverified fields ranked by number of components. Start from the top.

### Option C: Open a verification issue

Go to [New Issue → Field Verification](https://github.com/GEOS-ESM/GEOS_FieldDictionary/issues/new?template=field-verification.md) and fill in the standard name. This lets others see you're working on it and avoids duplicate effort.

---

## Step 2 — Look up the field

Find the entry in `geos_field_dictionary.yaml`. It looks like this:

```yaml
surface_temperature:
  long_name: Surface Temperature
  canonical_units: K
  verification_status: unverified
  conserved: false
  physical_dimension: temperature
  aliases: [TS]
  components: [SURFACE, MOIST]
```

---

## Step 3 — Check each field

### `long_name`

Should be a clear, human-readable description — this is what appears as the `long_name` attribute in NetCDF output.

- Auto-generated names are often fine for simple fields (`Air Temperature` ✓)
- Complex or GEOS-specific fields often need correction (`Surface Temperature` → `Surface Skin Temperature` ✓)
- Use title case. Keep it concise (under ~80 characters).

### `canonical_units`

The authoritative physical unit for this field in [UDUNITS-2](https://www.unidata.ucar.edu/software/udunits/) format.

Common correct forms:

| Quantity | Correct | Incorrect |
|---|---|---|
| Temperature | `K` | `Kelvin`, `degK` |
| Wind speed | `m s-1` | `m/s`, `ms-1` |
| Specific humidity | `kg kg-1` | `kg/kg` |
| Pressure | `Pa` or `hPa` | `pascal` |
| Flux | `W m-2` | `W/m2` |
| Dimensionless | `1` | `none`, `-` |

### `conserved`

Set to `true` if this field is a **conserved quantity** that must use conservative regridding:

- `true`: mass fractions, mixing ratios, specific humidity, tracer concentrations
- `false`: temperatures, winds, pressures, fluxes, diagnostics

When in doubt, `false` is the safer default.

### `physical_dimension`

Pick from the controlled vocabulary, or leave blank if genuinely uncertain:

```
temperature    pressure       density        velocity
mass_flux      mass_fraction  mole_fraction  energy
energy_flux    length         area           concentration
mixing_ratio   dimensionless  other
```

### `verification_status`

Promote the entry based on your review:

| Value | When to use |
|---|---|
| `unverified` | Leave as-is if you haven't reviewed it |
| `verified` | You've confirmed `long_name`, `canonical_units`, `conserved`, and `physical_dimension` are correct |
| `cf_compliant` | The standard name appears in the [CF standard names table](https://cfconventions.org/standard-names.html) AND all metadata is correct |

**How to check CF compliance:** Go to https://cfconventions.org/standard-names.html and search for the exact standard name (the dictionary key). If it's listed there with the same units and description, use `cf_compliant`.

### `provenance.verified_by`

Add your name. This creates an audit trail and lets others know who to ask questions.

---

## Step 4 — Edit the file

Open `geos_field_dictionary.yaml` in any text editor and update the entry. A fully verified entry looks like:

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

Key points:
- Keep the key (standard name) exactly as-is — do not rename it
- YAML indentation uses 2 spaces — do not use tabs
- Boolean values are `true` / `false` (lowercase, no quotes)
- String values do not need quotes unless they contain special characters

---

## Step 5 — Validate your change

Before submitting, run the validator to catch any formatting errors:

```bash
uv run utils/validate_schema.py --strict geos_field_dictionary.yaml
```

Expected output: `OK: geos_field_dictionary.yaml is valid.`

If it fails, check the error message — it will tell you exactly which field and which problem.

---

## Step 6 — Submit a Pull Request

1. Create a branch: `git checkout -b verify/surface_temperature`
2. Stage your change: `git add geos_field_dictionary.yaml`
3. Commit: `git commit -m "verify: surface_temperature"`
4. Push: `git push -u origin verify/surface_temperature`
5. Open a PR on GitHub. In the description, note what you changed and why (e.g., "Corrected long_name; confirmed CF-compliant per CF conventions table").

CI will automatically re-run the validator on your PR.

---

## FAQ

**Q: What if I'm not sure about `conserved`?**  
Leave it as `false` and note your uncertainty in the PR description. A reviewer can help.

**Q: What if the standard name itself seems wrong?**  
Open a separate issue rather than changing the key — renaming standard names affects MAPL and all downstream tools and requires broader team consensus.

**Q: What if `physical_dimension` isn't in the vocabulary?**  
Leave it blank or use `other`. If you believe a new category is needed, open an issue to discuss adding it to the vocabulary.

**Q: Can I verify multiple fields in one PR?**  
Yes — batching related fields (e.g., all wind fields, all temperature fields) in one PR is efficient and encouraged.

**Q: I found an entry with clearly wrong units. Should I fix it even if I don't know the whole picture?**  
Yes — a partial improvement (fixing `canonical_units` while leaving `verification_status: unverified`) is valuable. You don't need to fully verify an entry to fix an obvious error.

---

## Contact

Questions? Open a GitHub issue or email [mapl-support@lists.nasa.gov](mailto:mapl-support@lists.nasa.gov).
