"""
Reddit Layoffs Tracker - Main Entry Point

Usage:
    python main.py              # Scrape and analyze (no auth required)
    python main.py --analyze    # Analyze existing data only
"""

import argparse
from pathlib import Path

import yaml
from tqdm import tqdm

from src.scraper import (
    has_credentials,
    create_reddit_client,
    scrape_subreddit_public,
    scrape_subreddit_praw,
    scrape_comments_public,
)
from src.storage import save_posts_csv, save_posts_json, get_output_path
from src.analyzer import analyze_posts, print_analysis
import pandas as pd


def load_config() -> dict:
    """Load configuration from YAML file."""
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def scrape_all(config: dict) -> pd.DataFrame:
    """Scrape all configured subreddits."""
    all_posts = []

    subreddits = config["subreddits"]
    scrape_cfg = config["scraping"]

    # Check if we have API credentials
    use_praw = has_credentials()
    if use_praw:
        print("Using authenticated PRAW client")
        reddit = create_reddit_client()
    else:
        print("No API credentials found - using public JSON API")
        reddit = None

    for subreddit in subreddits:
        print(f"\nScraping r/{subreddit}...")

        if use_praw:
            post_gen = scrape_subreddit_praw(
                reddit,
                subreddit,
                limit=scrape_cfg["posts_per_subreddit"],
                sort_by=scrape_cfg["sort_by"],
                time_filter=scrape_cfg["time_filter"],
            )
        else:
            post_gen = scrape_subreddit_public(
                subreddit,
                limit=scrape_cfg["posts_per_subreddit"],
                sort_by=scrape_cfg["sort_by"],
                time_filter=scrape_cfg["time_filter"],
            )

        posts = list(
            tqdm(
                post_gen,
                desc=f"r/{subreddit}",
                total=scrape_cfg["posts_per_subreddit"],
            )
        )

        all_posts.extend(posts)
        print(f"  Fetched {len(posts)} posts")

        # Optionally scrape comments (public API only for now)
        if scrape_cfg.get("include_comments") and not use_praw:
            print(f"  Scraping comments...")
            all_comments = []
            for post in tqdm(posts[:30], desc="Comments"):  # Limit to top 30 posts
                comments = list(
                    scrape_comments_public(
                        post["id"],
                        subreddit,
                        limit=scrape_cfg["comments_per_post"],
                    )
                )
                all_comments.extend(comments)

            if all_comments:
                storage_cfg = config["storage"]
                ext = storage_cfg["format"]
                comments_path = get_output_path(
                    storage_cfg["data_dir"], subreddit, "comments", ext
                )
                if ext == "csv":
                    save_posts_csv(all_comments, comments_path)
                else:
                    save_posts_json(all_comments, comments_path)

    return pd.DataFrame(all_posts)


def main():
    parser = argparse.ArgumentParser(description="Reddit Layoffs Tracker")
    parser.add_argument(
        "--analyze",
        type=str,
        help="Path to existing CSV to analyze (skip scraping)",
    )
    args = parser.parse_args()

    config = load_config()

    if args.analyze:
        print(f"Loading data from {args.analyze}...")
        df = pd.read_csv(args.analyze, parse_dates=["created_utc"])
    else:
        df = scrape_all(config)

        if df.empty:
            print("No posts fetched!")
            return

        # Save posts
        storage_cfg = config["storage"]
        ext = storage_cfg["format"]
        posts_path = get_output_path(storage_cfg["data_dir"], "all", "posts", ext)

        if ext == "csv":
            save_posts_csv(df.to_dict("records"), posts_path)
        else:
            save_posts_json(df.to_dict("records"), posts_path)

    # Analyze
    stats = analyze_posts(df, config)
    print_analysis(stats)


if __name__ == "__main__":
    main()
