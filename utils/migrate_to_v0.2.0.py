#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""
migrate_to_v0.2.0.py — Migrate geos_field_dictionary.yaml from v0.1.x to v0.2.0.

Usage:
    uv run utils/migrate_to_v0.2.0.py [INPUT] [--output OUTPUT] [--cf-compliant CF_FILE]

Defaults:
    INPUT           geos_field_dictionary.yaml
    --output        geos_field_dictionary.yaml  (overwrites in place)
    --cf-compliant  cf_compliant_geos_long_names.txt

Transformations applied to each entry:
  - short_names  → aliases          (rename key, preserve values)
  - units        → canonical_units  (rename key, preserve values)
  - incomplete   → removed          (replaced by verification_status)
  - long_name    added              (auto-generated: underscores→spaces, title case)
  - conserved    added              (false by default; true for known conserved patterns)
  - verification_status added       (unverified by default; cf_compliant for 43 known fields)
  - physical_dimension added        (inferred from canonical_units where unambiguous)

Top-level structure changes:
  Flat mapping → field_dictionary.{version, metadata, entries}
"""

import sys
import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Unit → physical_dimension inference rules
# Rules are tried in order; first match wins.
# Each rule is (compiled_regex, dimension_string).
# ---------------------------------------------------------------------------
_UNIT_RULES = [
    # Temperature
    (re.compile(r"^K$"), "temperature"),
    (re.compile(r"^deg[_\s]?[CFK]$", re.IGNORECASE), "temperature"),
    # Pressure
    (re.compile(r"^(Pa|hPa|kPa|mbar|bar)$"), "pressure"),
    # Velocity / wind speed
    (re.compile(r"^m\s*s-1$"), "velocity"),
    (re.compile(r"^m\s*/\s*s$"), "velocity"),
    (re.compile(r"^cm\s*s-1$"), "velocity"),
    # Mass fraction / mixing ratio (dimensionless ratio by mass)
    (re.compile(r"^kg\s*kg-1$"), "mass_fraction"),
    (re.compile(r"^g\s*kg-1$"), "mass_fraction"),
    # Mole fraction
    (re.compile(r"^mol\s*mol-1$"), "mole_fraction"),
    (re.compile(r"^ppb(v)?$", re.IGNORECASE), "mole_fraction"),
    (re.compile(r"^ppm(v)?$", re.IGNORECASE), "mole_fraction"),
    (re.compile(r"^ppt(v)?$", re.IGNORECASE), "mole_fraction"),
    # Mass flux
    (re.compile(r"^kg\s*m-2\s*s-1$"), "mass_flux"),
    (re.compile(r"^g\s*m-2\s*s-1$"), "mass_flux"),
    # Energy flux / power per area
    (re.compile(r"^W\s*m-2$"), "energy_flux"),
    (re.compile(r"^J\s*m-2\s*s-1$"), "energy_flux"),
    # Energy
    (re.compile(r"^J\s*kg-1$"), "energy"),
    (re.compile(r"^J\s*m-2$"), "energy"),
    (re.compile(r"^J\s*m-3$"), "energy"),
    # Density
    (re.compile(r"^kg\s*m-3$"), "density"),
    (re.compile(r"^g\s*m-3$"), "density"),
    (re.compile(r"^kg\s*m-2$"), "density"),  # column mass density
    # Concentration (number or mass per volume)
    (re.compile(r"^m-3$"), "concentration"),
    (re.compile(r"^cm-3$"), "concentration"),
    (re.compile(r"^mol\s*m-3$"), "concentration"),
    (re.compile(r"^kg\s*m-3$"), "density"),
    # Length / height
    (re.compile(r"^m$"), "length"),
    (re.compile(r"^km$"), "length"),
    (re.compile(r"^cm$"), "length"),
    (re.compile(r"^mm$"), "length"),
    # Area
    (re.compile(r"^m2$"), "area"),
    (re.compile(r"^m\^2$"), "area"),
    (re.compile(r"^km2$"), "area"),
    # Volume
    (re.compile(r"^m3$"), "volume"),
    (re.compile(r"^m\^3$"), "volume"),
    # Frequency
    (re.compile(r"^s-1$"), "frequency"),
    (re.compile(r"^Hz$"), "frequency"),
    (re.compile(r"^rad\s*s-1$"), "angular_velocity"),
    # Dimensionless
    (re.compile(r"^1$"), "dimensionless"),
    (re.compile(r"^fraction$", re.IGNORECASE), "dimensionless"),
    (re.compile(r"^%$"), "dimensionless"),
    (re.compile(r"^none$", re.IGNORECASE), "dimensionless"),
    (re.compile(r"^-$"), "dimensionless"),
]

# Patterns in the standard name that suggest conserved=true
# (mass fractions, mixing ratios that are advected conservatively)
_CONSERVED_NAME_PATTERNS = [
    re.compile(r"mass_fraction_of_"),
    re.compile(r"mass_mixing_ratio"),
    re.compile(r"mixing_ratio"),
    re.compile(r"mole_fraction_of_"),
    re.compile(r"specific_humidity"),
    re.compile(r"mass_content_of_"),
]


def infer_physical_dimension(units: str) -> str | None:
    """Return a physical_dimension string for *units*, or None if unknown."""
    if not units:
        return None
    u = units.strip()
    for pattern, dimension in _UNIT_RULES:
        if pattern.match(u):
            return dimension
    return None


def infer_conserved(standard_name: str, units: str) -> bool:
    """Return True if the field is likely a conserved quantity."""
    for pattern in _CONSERVED_NAME_PATTERNS:
        if pattern.search(standard_name):
            return True
    # kg kg-1 fields are mass fractions — conserved unless name says otherwise
    if units and units.strip() == "kg kg-1":
        return True
    return False


def auto_long_name(standard_name: str) -> str:
    """Generate a human-readable long_name from a standard_name."""
    # Replace underscores and hyphens with spaces, title-case
    name = standard_name.replace("_", " ").replace("-", " ")
    # Title-case but preserve all-caps acronyms (e.g. CO, NH3, CLM4)
    words = []
    for word in name.split():
        if word.isupper() and len(word) > 1:
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words)


def load_cf_compliant(cf_file: Path) -> set:
    """Load the set of CF-compliant standard names from the text file."""
    if not cf_file.exists():
        print(f"WARNING: CF-compliant names file not found: {cf_file}", file=sys.stderr)
        return set()
    names = set()
    with open(cf_file, encoding="utf-8") as fh:
        for line in fh:
            name = line.strip()
            if name and not name.startswith("#"):
                names.add(name)
    return names


def migrate_entry(standard_name: str, old_entry: dict, cf_compliant_names: set) -> dict:
    """Convert a single v0.1.x entry dict to v0.2.0 format."""
    new = {}

    # --- long_name (required, new) ---
    new["long_name"] = auto_long_name(standard_name)

    # --- canonical_units (required, renamed from units) ---
    units = old_entry.get("units", "1")
    new["canonical_units"] = units if units else "1"

    # --- verification_status (required, replaces incomplete) ---
    if standard_name in cf_compliant_names:
        new["verification_status"] = "cf_compliant"
    else:
        new["verification_status"] = "unverified"

    # --- conserved (required, new) ---
    new["conserved"] = infer_conserved(standard_name, units)

    # --- physical_dimension (optional, new) ---
    dim = infer_physical_dimension(units)
    if dim:
        new["physical_dimension"] = dim

    # --- aliases (optional, renamed from short_names) ---
    short_names = old_entry.get("short_names")
    if short_names:
        new["aliases"] = short_names

    # --- components (optional, unchanged) ---
    components = old_entry.get("components")
    if components:
        new["components"] = components

    # Note: 'incomplete' is deliberately dropped.
    return new


def migrate(input_path: Path, output_path: Path, cf_file: Path) -> None:
    """Run the full migration and write the output file."""
    try:
        import yaml
    except ImportError:
        print(
            "ERROR: PyYAML is required. Run via: uv run utils/migrate_to_v0.2.0.py",
            file=sys.stderr,
        )
        sys.exit(2)

    # Load input
    print(f"Reading {input_path} ...")
    with open(input_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if data is None:
        print("ERROR: Input file is empty.", file=sys.stderr)
        sys.exit(1)

    if "field_dictionary" in data:
        print(
            "INFO: File already has a 'field_dictionary' wrapper — looks like v0.2.0 already. "
            "Re-running migration is a no-op for the structure, but will regenerate auto fields."
        )
        entries = data["field_dictionary"].get("entries", {})
    else:
        entries = data

    cf_compliant = load_cf_compliant(cf_file)
    print(f"Loaded {len(cf_compliant)} CF-compliant standard names from {cf_file}")

    # Migrate entries
    new_entries = {}
    n_cf = 0
    n_conserved = 0
    n_with_dim = 0
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            print(f"WARNING: Skipping non-mapping entry: {name!r}", file=sys.stderr)
            continue
        migrated = migrate_entry(str(name), entry, cf_compliant)
        new_entries[name] = migrated
        if migrated["verification_status"] == "cf_compliant":
            n_cf += 1
        if migrated["conserved"]:
            n_conserved += 1
        if "physical_dimension" in migrated:
            n_with_dim += 1

    total = len(new_entries)
    print(f"Migrated {total} entries:")
    print(f"  {n_cf} marked cf_compliant")
    print(f"  {total - n_cf} marked unverified")
    print(f"  {n_conserved} marked conserved=true")
    print(
        f"  {n_with_dim} with physical_dimension inferred ({total - n_with_dim} left blank)"
    )

    # Build v0.2.0 top-level structure
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output = {
        "field_dictionary": {
            "version": "0.2.0",
            "metadata": {
                "last_modified": now,
                "institution": "NASA GMAO",
                "contact": "mapl-support@lists.nasa.gov",
                "description": (
                    "GEOS field dictionary. Standard names follow CF conventions where "
                    "possible. See cf_compliant_geos_long_names.txt for verified CF entries."
                ),
            },
            "entries": new_entries,
        }
    }

    # Write output
    print(f"Writing {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as fh:
        yaml.dump(
            output,
            fh,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,
            width=120,
        )
    print("Done.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Migrate geos_field_dictionary.yaml from v0.1.x to v0.2.0 schema."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="geos_field_dictionary.yaml",
        help="Input YAML file (default: geos_field_dictionary.yaml)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output YAML file (default: same as input, overwrites in place)",
    )
    parser.add_argument(
        "--cf-compliant",
        default="cf_compliant_geos_long_names.txt",
        dest="cf_compliant",
        help="File listing CF-compliant standard names, one per line "
        "(default: cf_compliant_geos_long_names.txt)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path
    cf_file = Path(args.cf_compliant)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    migrate(input_path, output_path, cf_file)


if __name__ == "__main__":
    main()
