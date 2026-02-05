"""
Analyze layoffs by month and company.

Usage:
    python analyze_layoffs.py
"""

import re
from pathlib import Path
from collections import defaultdict
import glob

import pandas as pd
import yaml


def load_config() -> dict:
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def find_latest_data() -> Path:
    files = glob.glob("data/all_posts_*.csv")
    if not files:
        raise FileNotFoundError("No data files found. Run main.py first.")
    return Path(sorted(files)[-1])


def extract_companies(text: str, company_list: list[str]) -> list[str]:
    """Extract mentioned companies from text."""
    if not text or pd.isna(text):
        return []

    text_lower = text.lower()
    found = []

    for company in company_list:
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(company)

    return found


def main():
    config = load_config()
    companies = config.get("keywords", {}).get("companies", [])

    # Load data
    data_path = find_latest_data()
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path, parse_dates=["created_utc"])

    # Filter to last 6 months
    df["month"] = pd.to_datetime(df["created_utc"]).dt.to_period("M")
    latest_month = df["month"].max()
    six_months_ago = latest_month - 5
    df = df[df["month"] >= six_months_ago]

    print(f"Date range: {six_months_ago} to {latest_month}")
    print(f"Posts in range: {len(df)}")

    # Extract company mentions
    df["text_combined"] = df["title"].fillna("") + " " + df["selftext"].fillna("")
    df["companies_mentioned"] = df["text_combined"].apply(lambda x: extract_companies(x, companies))

    # Build month x company matrix
    month_company = defaultdict(lambda: defaultdict(int))

    for _, row in df.iterrows():
        month = str(row["month"])
        for company in row["companies_mentioned"]:
            month_company[month][company] += 1

    # Get all months and companies that appear
    all_months = sorted(month_company.keys())
    all_companies = set()
    for month_data in month_company.values():
        all_companies.update(month_data.keys())

    # Sort companies by total mentions
    company_totals = defaultdict(int)
    for month_data in month_company.values():
        for company, count in month_data.items():
            company_totals[company] += count

    sorted_companies = sorted(all_companies, key=lambda x: company_totals[x], reverse=True)

    # Create DataFrame
    table_data = []
    for company in sorted_companies:
        row = {"Company": company.capitalize()}
        for month in all_months:
            row[month] = month_company[month].get(company, 0)
        row["Total"] = company_totals[company]
        table_data.append(row)

    result_df = pd.DataFrame(table_data)

    # Print table
    print("\n" + "=" * 80)
    print("LAYOFF MENTIONS BY MONTH AND COMPANY (Reddit Posts)")
    print("=" * 80)
    print("\nNote: These are post counts mentioning each company, not actual layoff numbers.\n")

    # Format table nicely
    print(result_df.to_string(index=False))

    # Summary row
    print("\n" + "-" * 80)
    totals_row = {"Company": "TOTAL"}
    for month in all_months:
        totals_row[month] = sum(month_company[month].values())
    totals_row["Total"] = sum(company_totals.values())
    print(f"{'TOTAL':<12}", end="")
    for month in all_months:
        print(f"{totals_row[month]:>8}", end="")
    print(f"{totals_row['Total']:>8}")

    # Save to CSV
    output_path = Path("data/layoffs_by_month_company.csv")
    result_df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")

    # Top companies summary
    print("\n" + "=" * 80)
    print("TOP 10 COMPANIES BY MENTION COUNT")
    print("=" * 80)
    for i, (company, count) in enumerate(sorted(company_totals.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        bar = "█" * (count * 2)
        print(f"{i:2}. {company.capitalize():<12} {count:3} {bar}")


if __name__ == "__main__":
    main()
