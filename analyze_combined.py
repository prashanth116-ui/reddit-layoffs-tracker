"""
Combined analysis: Actual layoffs + Reddit sentiment.

Usage:
    python analyze_combined.py           # Full analysis
    python analyze_combined.py --save    # Save all charts
"""

import argparse
from pathlib import Path
import yaml

import pandas as pd

from src.layoffs_data import fetch_layoffs_data, clean_layoffs_data, get_layoffs_last_n_months
from src.sentiment import add_sentiment_to_df
from src.combined_analysis import (
    load_reddit_data,
    analyze_company_sentiment,
    combine_layoffs_and_sentiment,
    plot_layoffs_vs_mentions,
    plot_sentiment_by_layoff_size,
    plot_correlation_analysis,
    create_combined_dashboard,
    print_combined_summary,
)


def load_config() -> dict:
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Combined layoffs and sentiment analysis")
    parser.add_argument("--save", action="store_true", help="Save charts to data/")
    args = parser.parse_args()

    output_dir = Path("data") if args.save else None

    # Load config for company list
    config = load_config()
    companies = config.get("keywords", {}).get("companies", [])

    # Load Reddit data
    print("Loading Reddit data...")
    reddit_df = load_reddit_data()
    print(f"  Loaded {len(reddit_df)} Reddit posts")

    # Add sentiment
    print("Analyzing sentiment...")
    reddit_df = add_sentiment_to_df(reddit_df)

    # Load layoffs data
    print("\nLoading layoffs data...")
    layoffs_df = fetch_layoffs_data()
    layoffs_df = clean_layoffs_data(layoffs_df)
    layoffs_df = get_layoffs_last_n_months(layoffs_df, 6)
    print(f"  Loaded {len(layoffs_df)} layoff events")
    print(f"  Total laid off: {layoffs_df['laid_off_count'].sum():,}")

    # Analyze company sentiment in Reddit data
    print("\nAnalyzing company mentions and sentiment...")
    company_sentiment = analyze_company_sentiment(reddit_df, companies)
    print(f"  Found {len(company_sentiment)} companies mentioned in Reddit")

    # Combine datasets
    print("\nCombining datasets...")
    combined_df = combine_layoffs_and_sentiment(layoffs_df, company_sentiment)

    # Print summary
    print_combined_summary(combined_df)

    # Generate visualizations
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)

    print("\n[1/4] Layoffs vs Mentions scatter plot...")
    plot_layoffs_vs_mentions(combined_df, output_dir)

    print("\n[2/4] Sentiment by layoff size...")
    plot_sentiment_by_layoff_size(combined_df, output_dir)

    print("\n[3/4] Correlation analysis...")
    plot_correlation_analysis(combined_df, output_dir)

    print("\n[4/4] Combined dashboard...")
    create_combined_dashboard(combined_df, reddit_df, layoffs_df, output_dir)

    # Save combined data
    if args.save:
        combined_path = Path("data/combined_analysis.csv")
        combined_df.to_csv(combined_path, index=False)
        print(f"\nSaved combined data to: {combined_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
