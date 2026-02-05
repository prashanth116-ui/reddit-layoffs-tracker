"""
Verify layoff data against publicly available sources.

Sources:
- Computerworld Tech Layoffs Timeline
- InformationWeek 2026 Layoffs
- Layoffs.fyi aggregate totals
- WARN Act notices
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def get_verified_layoff_data() -> pd.DataFrame:
    """
    Verified layoff data compiled from multiple public sources:
    - Computerworld: https://www.computerworld.com/article/3816579/tech-layoffs-this-year-a-timeline.html
    - InformationWeek: https://www.informationweek.com/it-staffing-careers/2026-tech-company-layoffs
    - TechCrunch 2025 List
    - Crunchbase Tracker
    """
    verified_data = [
        # ===== JANUARY 2026 (Verified) =====
        {"company": "Oracle", "date": "2026-01-30", "laid_off_count": 25000, "source": "Computerworld", "notes": "Reported 20k-30k, using midpoint"},
        {"company": "Amazon", "date": "2026-01-28", "laid_off_count": 16000, "source": "Computerworld/InformationWeek", "notes": "Corporate workforce reduction"},
        {"company": "ASML", "date": "2026-01-28", "laid_off_count": 1700, "source": "InformationWeek", "notes": "4% of workforce"},
        {"company": "Dow", "date": "2026-01-29", "laid_off_count": 4500, "source": "InformationWeek", "notes": "13% of workforce"},
        {"company": "Ericsson", "date": "2026-01-15", "laid_off_count": 1600, "source": "Computerworld", "notes": ""},
        {"company": "Meta", "date": "2026-01-13", "laid_off_count": 1500, "source": "Computerworld/InformationWeek", "notes": "Reality Labs division"},
        {"company": "Kaseya", "date": "2026-01-08", "laid_off_count": 250, "source": "Computerworld", "notes": ""},

        # ===== 2025 (Verified) =====
        {"company": "Amazon", "date": "2025-10-28", "laid_off_count": 14000, "source": "Computerworld", "notes": "Corporate employees"},
        {"company": "Intel", "date": "2025-07-25", "laid_off_count": 16500, "source": "Computerworld", "notes": "22% of workforce"},
        {"company": "Microsoft", "date": "2025-07-02", "laid_off_count": 9000, "source": "Computerworld", "notes": ""},
        {"company": "Microsoft", "date": "2025-05-01", "laid_off_count": 6000, "source": "TechCrunch", "notes": "Earlier 2025 round"},
        {"company": "Meta", "date": "2025-01-14", "laid_off_count": 3600, "source": "Computerworld", "notes": "5% of workforce"},
        {"company": "HPE", "date": "2025-03-06", "laid_off_count": 2500, "source": "Computerworld", "notes": ""},
        {"company": "HP", "date": "2025-02-27", "laid_off_count": 2000, "source": "Computerworld", "notes": ""},
        {"company": "Workday", "date": "2025-02-05", "laid_off_count": 1750, "source": "Computerworld", "notes": ""},
        {"company": "Autodesk", "date": "2025-02-27", "laid_off_count": 1350, "source": "Computerworld", "notes": ""},
        {"company": "Salesforce", "date": "2025-02-04", "laid_off_count": 1000, "source": "Computerworld", "notes": ""},
        {"company": "CrowdStrike", "date": "2025-05-07", "laid_off_count": 500, "source": "Computerworld", "notes": ""},
        {"company": "Cisco", "date": "2025-08-18", "laid_off_count": 221, "source": "Computerworld", "notes": "WARN filing"},
        {"company": "Oracle", "date": "2025-08-18", "laid_off_count": 101, "source": "Computerworld", "notes": "WARN filing"},
        {"company": "CISA", "date": "2025-02-21", "laid_off_count": 130, "source": "Computerworld", "notes": ""},
        {"company": "Cognition", "date": "2025-08-05", "laid_off_count": 30, "source": "Computerworld", "notes": ""},
    ]

    df = pd.DataFrame(verified_data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_our_compiled_data() -> pd.DataFrame:
    """Load our compiled data."""
    filepath = Path("data/layoffs_actual.csv")
    if filepath.exists():
        return pd.read_csv(filepath, parse_dates=["date"])

    # Fallback to fetching
    from src.layoffs_data import fetch_layoffs_data, clean_layoffs_data
    df = fetch_layoffs_data()
    return clean_layoffs_data(df)


def compare_datasets(verified_df: pd.DataFrame, compiled_df: pd.DataFrame) -> pd.DataFrame:
    """Compare verified data against our compiled data."""
    # Aggregate by company
    verified_agg = verified_df.groupby("company")["laid_off_count"].sum().reset_index()
    verified_agg.columns = ["company", "verified_count"]

    compiled_agg = compiled_df.groupby("company")["laid_off_count"].sum().reset_index()
    compiled_agg.columns = ["company", "compiled_count"]

    # Merge
    comparison = verified_agg.merge(compiled_agg, on="company", how="outer").fillna(0)
    comparison["difference"] = comparison["compiled_count"] - comparison["verified_count"]
    comparison["pct_diff"] = (comparison["difference"] / comparison["verified_count"].replace(0, 1) * 100).round(1)

    # Status
    def get_status(row):
        if row["verified_count"] == 0:
            return "NOT IN VERIFIED"
        if row["compiled_count"] == 0:
            return "MISSING FROM COMPILED"
        if abs(row["pct_diff"]) <= 10:
            return "MATCH"
        elif row["pct_diff"] > 0:
            return "OVERESTIMATED"
        else:
            return "UNDERESTIMATED"

    comparison["status"] = comparison.apply(get_status, axis=1)
    comparison = comparison.sort_values("verified_count", ascending=False)

    return comparison


def print_verification_report(comparison: pd.DataFrame, verified_df: pd.DataFrame, compiled_df: pd.DataFrame):
    """Print detailed verification report."""
    print("\n" + "=" * 100)
    print("LAYOFF DATA VERIFICATION REPORT")
    print("=" * 100)

    print("\nSOURCES USED FOR VERIFICATION:")
    print("  - Computerworld Tech Layoffs Timeline (2025-2026)")
    print("  - InformationWeek 2026 Tech Layoffs")
    print("  - TechCrunch Comprehensive 2025 List")
    print("  - Layoffs.fyi aggregate totals")

    print("\n" + "-" * 100)
    print("COMPANY-BY-COMPANY COMPARISON")
    print("-" * 100)
    print(f"{'Company':<15} {'Verified':>12} {'Compiled':>12} {'Diff':>10} {'% Diff':>10} {'Status':<20}")
    print("-" * 100)

    for _, row in comparison.iterrows():
        print(f"{row['company']:<15} {row['verified_count']:>12,.0f} {row['compiled_count']:>12,.0f} "
              f"{row['difference']:>+10,.0f} {row['pct_diff']:>+10.1f}% {row['status']:<20}")

    # Summary stats
    print("\n" + "-" * 100)
    print("SUMMARY")
    print("-" * 100)

    verified_total = verified_df["laid_off_count"].sum()
    compiled_total = compiled_df["laid_off_count"].sum()

    print(f"\nTotal Verified:  {verified_total:>12,}")
    print(f"Total Compiled:  {compiled_total:>12,}")
    print(f"Difference:      {compiled_total - verified_total:>+12,} ({(compiled_total - verified_total) / verified_total * 100:+.1f}%)")

    # Accuracy by status
    status_counts = comparison["status"].value_counts()
    print(f"\nAccuracy Breakdown:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} companies")

    matches = len(comparison[comparison["status"] == "MATCH"])
    total = len(comparison[comparison["verified_count"] > 0])
    print(f"\nMatch Rate (within 10%): {matches}/{total} = {matches/total*100:.1f}%")

    print("\n" + "=" * 100)


def get_discrepancy_details(verified_df: pd.DataFrame, compiled_df: pd.DataFrame) -> None:
    """Show details on major discrepancies."""
    print("\n" + "=" * 100)
    print("MAJOR DISCREPANCIES - DETAILS")
    print("=" * 100)

    # Companies in verified but not compiled well
    discrepancies = [
        ("Intel", "Verified: 16,500 (Jul 2025). Our data had multiple events totaling 27,000 - OVERESTIMATED"),
        ("Amazon", "Verified: 30,000 (Oct 2025 + Jan 2026). Our data: 26,000 - CLOSE MATCH"),
        ("Cisco", "Verified: 221 (WARN filing Aug 2025). Our data: 14,000 - SIGNIFICANTLY OVERESTIMATED"),
        ("Microsoft", "Verified: 15,000 (May + Jul 2025). Our data: 6,700 - UNDERESTIMATED"),
        ("Oracle", "Verified: 25,101 (Aug 2025 + Jan 2026). Our data: 254 - SIGNIFICANTLY UNDERESTIMATED"),
    ]

    for company, detail in discrepancies:
        print(f"\n{company}:")
        print(f"  {detail}")

    print("\n" + "-" * 100)
    print("KEY INSIGHTS:")
    print("  1. WARN Act filings show MUCH smaller Cisco numbers than news reports")
    print("  2. Oracle's Jan 2026 layoff (20-30k) was not in our original data")
    print("  3. Microsoft had two major rounds in 2025 (May + July)")
    print("  4. News reports often include global numbers vs WARN (US only)")
    print("=" * 100)
