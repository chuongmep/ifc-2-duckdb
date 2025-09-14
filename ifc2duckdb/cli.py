"""Command-line interface for ifc2duckdb."""

import argparse
import logging
import sys
from pathlib import Path

import ifcopenshell

from .patcher import Patcher


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Convert IFC files to DuckDB format for fast analysis and querying",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ifc2duckdb input.ifc output.duckdb
  ifc2duckdb input.ifc --database output.duckdb --no-geometry
  ifc2duckdb input.ifc --database output.duckdb --verbose
        """,
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input IFC file",
    )

    parser.add_argument(
        "--database",
        "-d",
        type=str,
        default="database.duckdb",
        help="Path to the output DuckDB database file (default: database.duckdb)",
    )

    parser.add_argument(
        "--no-full-schema",
        action="store_true",
        help="Only create tables for IFC classes present in the file "
        "(default: create full schema)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict mode for data type validation",
    )

    parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand entity lists into separate rows",
    )

    parser.add_argument(
        "--no-inverses",
        action="store_true",
        help="Skip inverse relationship data",
    )

    parser.add_argument(
        "--no-psets",
        action="store_true",
        help="Skip property set data",
    )

    parser.add_argument(
        "--no-geometry",
        action="store_true",
        help="Skip geometry data",
    )

    parser.add_argument(
        "--skip-geometry-data",
        action="store_true",
        help="Skip geometry data for representation tables",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() == ".ifc":
        print(
            f"Warning: Input file '{args.input_file}' does not have .ifc extension.",
            file=sys.stderr,
        )

    try:
        # Load IFC file
        print(f"Loading IFC file: {args.input_file}")
        ifc_file = ifcopenshell.open(str(input_path))
        print(f"IFC file loaded successfully. Schema: {ifc_file.schema}")

        # Create patcher
        patcher = Patcher(
            file=ifc_file,
            database=args.database,
            full_schema=not args.no_full_schema,
            is_strict=args.strict,
            should_expand=args.expand,
            should_get_inverses=not args.no_inverses,
            should_get_psets=not args.no_psets,
            should_get_geometry=not args.no_geometry,
            should_skip_geometry_data=args.skip_geometry_data,
        )

        # Convert to DuckDB
        print(f"Converting to DuckDB: {args.database}")
        patcher.patch()

        output_path = patcher.get_output()
        if output_path:
            print("Conversion completed successfully!")
            print(f"Output database: {output_path}")
        else:
            print(
                "Error: Conversion failed - no output file generated.", file=sys.stderr
            )
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
