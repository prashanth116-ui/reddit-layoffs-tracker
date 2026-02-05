"""
Visualize Reddit Layoffs Data

Usage:
    python visualize.py                          # Full visualization suite
    python visualize.py --dashboard              # Main dashboard only
    python visualize.py --sentiment              # Sentiment analysis only
    python visualize.py --save                   # Save all plots to data/
"""

import argparse
from pathlib import Path
import glob

import pandas as pd
import yaml

from src.visualize import (
    plot_posts_over_time,
    plot_company_mentions,
    plot_score_distribution,
    plot_engagement_scatter,
    plot_weekly_trend,
    plot_top_posts,
    create_dashboard,
    plot_sentiment_distribution,
    plot_sentiment_over_time,
    plot_sentiment_vs_engagement,
    create_sentiment_dashboard,
)
from src.analyzer import analyze_posts
from src.sentiment import add_sentiment_to_df, get_sentiment_summary, print_sentiment_summary


def load_config() -> dict:
    """Load configuration from YAML file."""
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def find_latest_data() -> Path:
    """Find the most recent posts CSV file."""
    files = glob.glob("data/all_posts_*.csv")
    if not files:
        raise FileNotFoundError("No data files found in data/. Run main.py first.")
    return Path(sorted(files)[-1])


def main():
    parser = argparse.ArgumentParser(description="Visualize Reddit Layoffs Data")
    parser.add_argument("file", nargs="?", help="Path to posts CSV file")
    parser.add_argument("--dashboard", action="store_true", help="Show main dashboard only")
    parser.add_argument("--sentiment", action="store_true", help="Show sentiment analysis only")
    parser.add_argument("--save", action="store_true", help="Save plots to data/ folder")
    args = parser.parse_args()

    # Find data file
    if args.file:
        data_path = Path(args.file)
    else:
        data_path = find_latest_data()

    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path, parse_dates=["created_utc"])
    print(f"Loaded {len(df)} posts")

    # Get config and analyze
    config = load_config()
    stats = analyze_posts(df, config)

    # Output directory
    output_dir = Path("data") if args.save else None

    if args.dashboard:
        create_dashboard(df, stats, output_dir)
    elif args.sentiment:
        # Sentiment analysis
        df = add_sentiment_to_df(df)
        summary = get_sentiment_summary(df)
        print_sentiment_summary(summary)

        print("\n[1/3] Sentiment Distribution...")
        df = plot_sentiment_distribution(df, output_dir)

        print("\n[2/3] Sentiment Over Time...")
        df = plot_sentiment_over_time(df, output_dir)

        print("\n[3/3] Sentiment Dashboard...")
        df = create_sentiment_dashboard(df, output_dir)
    else:
        # Full suite
        print("\n[1/8] Weekly Trend...")
        plot_weekly_trend(df, output_dir)

        print("\n[2/8] Company Mentions...")
        plot_company_mentions(stats, output_dir)

        print("\n[3/8] Score Distribution...")
        plot_score_distribution(df, output_dir)

        print("\n[4/8] Engagement Scatter...")
        plot_engagement_scatter(df, output_dir)

        print("\n[5/8] Top Posts...")
        plot_top_posts(df, 10, output_dir)

        print("\n[6/8] Main Dashboard...")
        create_dashboard(df, stats, output_dir)

        print("\n[7/8] Sentiment Analysis...")
        df = add_sentiment_to_df(df)
        summary = get_sentiment_summary(df)
        print_sentiment_summary(summary)
        df = plot_sentiment_distribution(df, output_dir)

        print("\n[8/8] Sentiment Dashboard...")
        df = create_sentiment_dashboard(df, output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
