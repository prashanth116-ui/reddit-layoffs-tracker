"""
Verify our compiled layoff data against public sources.

Usage:
    python verify_layoffs.py
    python verify_layoffs.py --update  # Update with verified data
"""

import argparse
from pathlib import Path

import pandas as pd

from src.verify_data import (
    get_verified_layoff_data,
    get_our_compiled_data,
    compare_datasets,
    print_verification_report,
    get_discrepancy_details,
)


def main():
    parser = argparse.ArgumentParser(description="Verify layoff data")
    parser.add_argument("--update", action="store_true", help="Update data with verified numbers")
    parser.add_argument("--save", action="store_true", help="Save comparison to CSV")
    args = parser.parse_args()

    print("Loading verified data from public sources...")
    verified_df = get_verified_layoff_data()
    print(f"  Verified records: {len(verified_df)}")
    print(f"  Verified total: {verified_df['laid_off_count'].sum():,}")

    print("\nLoading our compiled data...")
    compiled_df = get_our_compiled_data()
    print(f"  Compiled records: {len(compiled_df)}")
    print(f"  Compiled total: {compiled_df['laid_off_count'].sum():,}")

    # Compare
    comparison = compare_datasets(verified_df, compiled_df)

    # Print report
    print_verification_report(comparison, verified_df, compiled_df)

    # Show discrepancy details
    get_discrepancy_details(verified_df, compiled_df)

    # Save comparison
    if args.save:
        comparison_path = Path("data/verification_comparison.csv")
        comparison.to_csv(comparison_path, index=False)
        print(f"\nSaved comparison to: {comparison_path}")

    # Update with verified data
    if args.update:
        print("\nUpdating with verified data...")
        verified_path = Path("data/layoffs_verified.csv")
        verified_df.to_csv(verified_path, index=False)
        print(f"Saved verified data to: {verified_path}")


if __name__ == "__main__":
    main()
