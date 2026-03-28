---
name: Field Verification
about: Verify and improve metadata for a field dictionary entry
title: "Verify: <standard_name>"
labels: []
assignees: ''
---

## Field: `<standard_name>`

Replace `<standard_name>` with the exact key from `geos_field_dictionary.yaml`.

---

### Current Metadata

Paste the current entry here (search `geos_field_dictionary.yaml` for the standard name):

```yaml
# paste entry here
```

---

### Verification Checklist

- [ ] `long_name` is accurate and suitable for NetCDF output
- [ ] `canonical_units` is correct and UDUNITS-2 compatible
- [ ] `physical_dimension` is appropriate (or confirmed as unknown)
- [ ] `conserved` flag is correct (is this a conserved quantity requiring conservative regridding?)
- [ ] Check [CF standard names table](https://cfconventions.org/standard-names.html) — is this field CF-compliant?
- [ ] `verification_status` updated to `verified` or `cf_compliant`
- [ ] `provenance.verified_by` populated with your name

---

### Proposed Updated Entry

```yaml
<standard_name>:
  long_name: <human-readable description>
  canonical_units: <UDUNITS-2 string>
  verification_status: verified   # or cf_compliant
  conserved: false                # true if mass/energy conserved quantity
  physical_dimension: <category>  # from controlled vocabulary, or omit if unknown
  provenance:
    verified_by: <Your Name>
  aliases: [<short names>]
  components: [<GEOS components>]
```

---

### Notes

<!-- Any additional context, references to CF conventions, MAPL usage, etc. -->

---

### References

- [CF Standard Names](https://cfconventions.org/standard-names.html)
- [UDUNITS-2 unit strings](https://www.unidata.ucar.edu/software/udunits/)
- [Physical dimension vocabulary](../blob/main/README.md#physical_dimension)
- [Verification guide](../blob/main/CONTRIBUTING.md#field-verification-workflow)
