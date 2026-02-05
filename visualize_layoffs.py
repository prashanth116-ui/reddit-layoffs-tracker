"""
Visualize actual layoff data.

Usage:
    python visualize_layoffs.py                # Full visualization suite
    python visualize_layoffs.py --dashboard    # Dashboard only
    python visualize_layoffs.py --save         # Save all charts
"""

import argparse
from pathlib import Path

import pandas as pd

from src.layoffs_data import (
    fetch_layoffs_data,
    clean_layoffs_data,
    get_layoffs_last_n_months,
)
from src.layoffs_viz import (
    plot_monthly_trend,
    plot_top_companies,
    plot_industry_breakdown,
    plot_company_timeline,
    plot_stacked_area,
    create_layoffs_dashboard,
)


def main():
    parser = argparse.ArgumentParser(description="Visualize layoff data")
    parser.add_argument("--months", type=int, default=6, help="Number of months")
    parser.add_argument("--dashboard", action="store_true", help="Dashboard only")
    parser.add_argument("--save", action="store_true", help="Save charts")
    args = parser.parse_args()

    # Fetch and prepare data
    print("Loading layoff data...\n")
    df = fetch_layoffs_data()
    df = clean_layoffs_data(df)
    df = get_layoffs_last_n_months(df, args.months)

    total = df['laid_off_count'].sum()
    print(f"Total layoffs in last {args.months} months: {total:,}")
    print(f"Companies affected: {df['company'].nunique()}")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")

    # Output directory
    output_dir = Path("data") if args.save else None

    if args.dashboard:
        print("\nGenerating dashboard...")
        create_layoffs_dashboard(df, output_dir)
    else:
        print("\n[1/5] Monthly Trend...")
        plot_monthly_trend(df, output_dir)

        print("\n[2/5] Top Companies...")
        plot_top_companies(df, 15, output_dir)

        print("\n[3/5] Industry Breakdown...")
        plot_industry_breakdown(df, output_dir)

        print("\n[4/5] Company Timeline Heatmap...")
        plot_company_timeline(df, 10, output_dir)

        print("\n[5/5] Dashboard...")
        create_layoffs_dashboard(df, output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
