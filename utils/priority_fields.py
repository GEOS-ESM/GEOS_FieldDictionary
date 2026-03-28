#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""
priority_fields.py — Identify the highest-priority unverified fields for review.

Fields are ranked by number of GEOS components that use them (a proxy for
impact). The top N are printed in a format suitable for pasting into a
GitHub issue or team planning doc.

Usage:
    uv run utils/priority_fields.py [--top N] [--status STATUS] [--all-statuses]
                                    [--format FORMAT] [FILE]

Defaults:
    FILE        geos_field_dictionary.yaml
    --top       100
    --status    unverified
    --format    table

Examples:
    # Top 50 unverified fields
    uv run utils/priority_fields.py --top 50

    # All cf_compliant fields ranked by component count
    uv run utils/priority_fields.py --status cf_compliant

    # All statuses, markdown output
    uv run utils/priority_fields.py --all-statuses --format markdown
"""

import sys
import argparse
from pathlib import Path


def load_entries(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        print(
            "ERROR: PyYAML required. Run via: uv run utils/priority_fields.py",
            file=sys.stderr,
        )
        sys.exit(2)

    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if "field_dictionary" in data:
        return data["field_dictionary"].get("entries", {})
    return data  # v0.1.x fallback


def rank_fields(entries: dict, statuses: set | None) -> list[dict]:
    """Return entries sorted by component count descending."""
    rows = []
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        status = entry.get("verification_status", "unverified")
        if statuses is not None and status not in statuses:
            continue
        components = entry.get("components") or []
        rows.append(
            {
                "name": name,
                "status": status,
                "components": len(components),
                "component_list": components,
                "long_name": entry.get("long_name", ""),
                "canonical_units": entry.get("canonical_units", ""),
                "physical_dimension": entry.get("physical_dimension", ""),
                "conserved": entry.get("conserved", False),
            }
        )
    rows.sort(key=lambda r: (-r["components"], r["name"]))
    return rows


def print_table(rows: list[dict], top: int) -> None:
    subset = rows[:top]
    if not subset:
        print("No matching fields found.")
        return

    # Column widths
    name_w = max(len(r["name"]) for r in subset)
    name_w = max(name_w, 13)
    unit_w = max(len(r["canonical_units"]) for r in subset)
    unit_w = max(unit_w, 14)
    dim_w = max(len(r["physical_dimension"]) for r in subset)
    dim_w = max(dim_w, 9)

    header = (
        f"{'Rank':<5} {'Standard Name':<{name_w}}  {'Units':<{unit_w}}  "
        f"{'Dimension':<{dim_w}}  {'Con':>3}  {'Comps':>5}  Status"
    )
    sep = "-" * len(header)
    print(header)
    print(sep)
    for i, r in enumerate(subset, 1):
        print(
            f"{i:<5} {r['name']:<{name_w}}  {r['canonical_units']:<{unit_w}}  "
            f"{r['physical_dimension']:<{dim_w}}  {'Y' if r['conserved'] else 'N':>3}  "
            f"{r['components']:>5}  {r['status']}"
        )
    print(sep)
    print(f"Showing {len(subset)} of {len(rows)} matching fields.")


def print_markdown(rows: list[dict], top: int) -> None:
    subset = rows[:top]
    if not subset:
        print("No matching fields found.")
        return

    print(
        f"| # | Standard Name | Units | Dimension | Conserved | Components | Status |"
    )
    print(f"|---|---|---|---|---|---|---|")
    for i, r in enumerate(subset, 1):
        print(
            f"| {i} | `{r['name']}` | `{r['canonical_units']}` | "
            f"{r['physical_dimension'] or '—'} | "
            f"{'yes' if r['conserved'] else 'no'} | "
            f"{r['components']} | {r['status']} |"
        )
    print(f"\n_{len(subset)} of {len(rows)} matching fields shown._")


def parse_args():
    parser = argparse.ArgumentParser(
        description="List highest-priority unverified fields ranked by component usage."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="geos_field_dictionary.yaml",
        help="Path to the YAML dictionary (default: geos_field_dictionary.yaml)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        metavar="N",
        help="Number of fields to show (default: 100)",
    )
    parser.add_argument(
        "--status",
        default="unverified",
        choices=["unverified", "verified", "cf_compliant"],
        help="Filter by verification_status (default: unverified)",
    )
    parser.add_argument(
        "--all-statuses",
        action="store_true",
        help="Include fields of all verification statuses",
    )
    parser.add_argument(
        "--format",
        default="table",
        choices=["table", "markdown"],
        help="Output format (default: table)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)

    entries = load_entries(path)
    statuses = None if args.all_statuses else {args.status}
    rows = rank_fields(entries, statuses)

    status_label = "all statuses" if args.all_statuses else f"status={args.status}"
    print(f"# Priority Fields — {status_label}, ranked by component count\n")

    if args.format == "markdown":
        print_markdown(rows, args.top)
    else:
        print_table(rows, args.top)


if __name__ == "__main__":
    main()
