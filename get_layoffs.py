"""
Fetch and display actual layoff data from multiple sources.

Usage:
    python get_layoffs.py           # Last 6 months, top 20 companies
    python get_layoffs.py --months 12 --top 30
"""

import argparse
from pathlib import Path

import pandas as pd

from src.layoffs_data import (
    fetch_layoffs_data,
    clean_layoffs_data,
    get_layoffs_last_n_months,
    tabulate_by_month_company,
    print_layoffs_table,
)


def main():
    parser = argparse.ArgumentParser(description="Fetch actual layoff data")
    parser.add_argument("--months", type=int, default=6, help="Number of months to include")
    parser.add_argument("--top", type=int, default=20, help="Top N companies to show")
    parser.add_argument("--save", action="store_true", help="Save to CSV")
    args = parser.parse_args()

    # Fetch data
    print("Fetching layoff data...\n")
    df = fetch_layoffs_data()

    if df is None or df.empty:
        print("No data available")
        return

    # Clean data
    df = clean_layoffs_data(df)

    print(f"Total records: {len(df)}")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")

    # Filter to last N months
    df_filtered = get_layoffs_last_n_months(df, args.months)
    print(f"Records in last {args.months} months: {len(df_filtered)}")

    if df_filtered.empty:
        print("No data in specified date range")
        return

    # Create pivot table
    pivot = tabulate_by_month_company(df_filtered, args.top)

    # Print results
    print_layoffs_table(df_filtered, pivot)

    # Save if requested
    if args.save:
        Path("data").mkdir(exist_ok=True)

        # Save raw filtered data
        raw_path = Path("data/layoffs_actual.csv")
        df_filtered.to_csv(raw_path, index=False)
        print(f"\nSaved raw data to: {raw_path}")

        # Save pivot table
        pivot_path = Path("data/layoffs_by_month_company_actual.csv")
        pivot.to_csv(pivot_path)
        print(f"Saved pivot table to: {pivot_path}")


if __name__ == "__main__":
    main()
