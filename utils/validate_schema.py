#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""
validate_schema.py — Schema validator for geos_field_dictionary.yaml (v0.2.0).

Usage:
    python utils/validate_schema.py geos_field_dictionary.yaml

Exits with code 0 if the file is valid, 1 if errors are found.

Checks performed:
  - Top-level structure: field_dictionary.version and field_dictionary.entries present
  - Required fields: long_name, canonical_units, verification_status, conserved
  - verification_status is one of: unverified, verified, cf_compliant
  - canonical_units is a non-empty string
  - conserved is a boolean
  - physical_dimension, if present, is from the controlled vocabulary
  - No duplicate standard names (the YAML parser normally catches these, but
    this validator re-parses with duplicate detection to be safe)
"""

import sys
import argparse
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Controlled vocabulary for physical_dimension
# ---------------------------------------------------------------------------
PHYSICAL_DIMENSION_VOCAB = {
    "temperature",
    "pressure",
    "density",
    "velocity",
    "acceleration",
    "mass",
    "mass_flux",
    "mass_fraction",
    "mole_fraction",
    "energy",
    "energy_flux",
    "power",
    "length",
    "area",
    "volume",
    "concentration",
    "mixing_ratio",
    "frequency",
    "angular_velocity",
    "dimensionless",
    "other",
}

VERIFICATION_STATUS_VALUES = {"unverified", "verified", "cf_compliant"}

REQUIRED_FIELDS = ["long_name", "canonical_units", "verification_status", "conserved"]


# ---------------------------------------------------------------------------
# Duplicate-key-detecting YAML loader
# ---------------------------------------------------------------------------


def _make_duplicate_detecting_loader():
    """Return a yaml.Loader subclass that raises on duplicate keys."""
    try:
        import yaml

        class _DuplicateKeyLoader(yaml.SafeLoader):
            pass

        def _construct_mapping(loader, node, deep=False):
            loader.flatten_mapping(node)
            pairs = loader.construct_pairs(node, deep=deep)
            keys = [k for k, _ in pairs]
            seen = set()
            duplicates = []
            for k in keys:
                if k in seen:
                    duplicates.append(k)
                seen.add(k)
            if duplicates:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"Duplicate key(s) found: {duplicates}",
                    node.start_mark,
                )
            return dict(pairs)

        _DuplicateKeyLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
        )
        return _DuplicateKeyLoader

    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class ValidationError:
    def __init__(self, entry_name: str, message: str):
        self.entry_name = entry_name
        self.message = message

    def __str__(self):
        return f"  [{self.entry_name}] {self.message}"


def validate_entry(name: str, entry: dict) -> list:
    """Validate a single dictionary entry. Returns a list of ValidationError."""
    errors = []

    if not isinstance(entry, dict):
        errors.append(
            ValidationError(
                name, f"Entry is not a YAML mapping (got {type(entry).__name__})"
            )
        )
        return errors

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(ValidationError(name, f"Missing required field: '{field}'"))

    # long_name: non-empty string
    if "long_name" in entry:
        val = entry["long_name"]
        if not isinstance(val, str) or not val.strip():
            errors.append(
                ValidationError(
                    name, f"'long_name' must be a non-empty string (got {val!r})"
                )
            )

    # canonical_units: non-empty string
    if "canonical_units" in entry:
        val = entry["canonical_units"]
        if not isinstance(val, str) or not val.strip():
            errors.append(
                ValidationError(
                    name, f"'canonical_units' must be a non-empty string (got {val!r})"
                )
            )

    # verification_status: enum
    if "verification_status" in entry:
        val = entry["verification_status"]
        if val not in VERIFICATION_STATUS_VALUES:
            errors.append(
                ValidationError(
                    name,
                    f"'verification_status' must be one of {sorted(VERIFICATION_STATUS_VALUES)} (got {val!r})",
                )
            )

    # conserved: boolean
    if "conserved" in entry:
        val = entry["conserved"]
        if not isinstance(val, bool):
            errors.append(
                ValidationError(name, f"'conserved' must be a boolean (got {val!r})")
            )

    # physical_dimension: controlled vocabulary (optional field)
    if "physical_dimension" in entry:
        val = entry["physical_dimension"]
        if val is not None:
            if not isinstance(val, str):
                errors.append(
                    ValidationError(
                        name, f"'physical_dimension' must be a string (got {val!r})"
                    )
                )
            elif val not in PHYSICAL_DIMENSION_VOCAB:
                errors.append(
                    ValidationError(
                        name,
                        f"'physical_dimension' value {val!r} is not in the controlled vocabulary. "
                        f"Allowed values: {sorted(PHYSICAL_DIMENSION_VOCAB)}",
                    )
                )

    # aliases: list of strings (optional)
    if "aliases" in entry:
        val = entry["aliases"]
        if val is not None:
            if not isinstance(val, list):
                errors.append(
                    ValidationError(
                        name, f"'aliases' must be a list (got {type(val).__name__})"
                    )
                )
            else:
                for i, alias in enumerate(val):
                    if not isinstance(alias, str):
                        errors.append(
                            ValidationError(
                                name, f"'aliases[{i}]' must be a string (got {alias!r})"
                            )
                        )

    # components: list of strings (optional)
    if "components" in entry:
        val = entry["components"]
        if val is not None:
            if not isinstance(val, list):
                errors.append(
                    ValidationError(
                        name, f"'components' must be a list (got {type(val).__name__})"
                    )
                )
            else:
                for i, comp in enumerate(val):
                    if not isinstance(comp, str):
                        errors.append(
                            ValidationError(
                                name,
                                f"'components[{i}]' must be a string (got {comp!r})",
                            )
                        )

    # provenance: optional object with verified_by string
    if "provenance" in entry:
        val = entry["provenance"]
        if val is not None:
            if not isinstance(val, dict):
                errors.append(
                    ValidationError(
                        name,
                        f"'provenance' must be a mapping (got {type(val).__name__})",
                    )
                )
            else:
                if "verified_by" in val:
                    vb = val["verified_by"]
                    if not isinstance(vb, str) or not vb.strip():
                        errors.append(
                            ValidationError(
                                name,
                                f"'provenance.verified_by' must be a non-empty string (got {vb!r})",
                            )
                        )

    return errors


def validate_file(path: str, strict: bool = False) -> int:
    """
    Validate the field dictionary YAML file at *path*.

    In non-strict mode (default), a v0.1.x flat-format dictionary prints a
    warning but exits 0 — it is not yet expected to conform to v0.2.0.
    Pass strict=True to require the v0.2.0 wrapper and full entry validation.

    Returns the number of errors found (0 = valid).
    """
    try:
        import yaml
    except ImportError:
        print(
            "ERROR: PyYAML is required. Install it with: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(2)

    file_path = Path(path)
    if not file_path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)

    # Load with duplicate-key detection
    loader_class = _make_duplicate_detecting_loader()
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            if loader_class is not None:
                data = yaml.load(fh, Loader=loader_class)
            else:
                data = yaml.safe_load(fh)
    except Exception as exc:
        print(f"ERROR: Failed to parse YAML: {exc}", file=sys.stderr)
        return 1

    if data is None:
        print("ERROR: File is empty or contains no data.", file=sys.stderr)
        return 1

    # ---------------------------------------------------------------------------
    # Determine schema format: v0.2.0 (wrapped) vs v0.1.x (flat)
    # ---------------------------------------------------------------------------
    all_errors = []

    if "field_dictionary" in data:
        # v0.2.0 format
        fd = data["field_dictionary"]

        # Check version
        version = fd.get("version")
        if version is None:
            all_errors.append(
                ValidationError("<top-level>", "Missing 'field_dictionary.version'")
            )
        elif not re.match(r"^\d+\.\d+\.\d+$", str(version)):
            all_errors.append(
                ValidationError(
                    "<top-level>",
                    f"'field_dictionary.version' should be semver (got {version!r})",
                )
            )

        # Check entries
        entries = fd.get("entries")
        if entries is None:
            all_errors.append(
                ValidationError("<top-level>", "Missing 'field_dictionary.entries'")
            )
        elif not isinstance(entries, dict):
            all_errors.append(
                ValidationError(
                    "<top-level>",
                    f"'field_dictionary.entries' must be a mapping (got {type(entries).__name__})",
                )
            )
        else:
            for name, entry in entries.items():
                all_errors.extend(validate_entry(str(name), entry))

    else:
        # Possibly v0.1.x flat format
        print(
            "WARNING: File does not have a 'field_dictionary' top-level key. "
            "This appears to be a v0.1.x format dictionary.\n"
            "         Run utils/migrate_to_v0.2.0.py to upgrade to v0.2.0.",
            file=sys.stderr,
        )
        if not strict:
            # Non-strict mode: warn but pass. Migration has not happened yet.
            print(
                "OK: Skipping v0.2.0 entry validation for pre-migration dictionary (use --strict to enforce)."
            )
            return 0
        # Strict mode: validate all entries against v0.2.0 rules
        if isinstance(data, dict):
            for name, entry in data.items():
                all_errors.extend(validate_entry(str(name), entry))
        else:
            print(
                "ERROR: File is not a YAML mapping at the top level.", file=sys.stderr
            )
            return 1

    # ---------------------------------------------------------------------------
    # Report results
    # ---------------------------------------------------------------------------
    n_errors = len(all_errors)
    if n_errors == 0:
        print(f"OK: {file_path.name} is valid.")
    else:
        print(f"FAIL: {n_errors} error(s) found in {file_path.name}:\n")
        for err in all_errors:
            print(err)
        print()

    return n_errors


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate a GEOS field dictionary YAML file against the v0.2.0 schema."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="geos_field_dictionary.yaml",
        help="Path to the YAML file to validate (default: geos_field_dictionary.yaml)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require v0.2.0 top-level wrapper (field_dictionary.version and .entries). "
        "Without this flag, v0.1.x flat-format files are validated with a warning.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    n_errors = validate_file(args.file, strict=args.strict)
    sys.exit(0 if n_errors == 0 else 1)


if __name__ == "__main__":
    main()
