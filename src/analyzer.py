"""Analysis utilities for layoff data."""

import re
from collections import Counter
from datetime import datetime

import pandas as pd


def extract_companies(text: str, company_list: list[str]) -> list[str]:
    """Extract mentioned companies from text."""
    if not text:
        return []

    text_lower = text.lower()
    found = []

    for company in company_list:
        # Word boundary match to avoid partial matches
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(company)

    return found


def analyze_posts(df: pd.DataFrame, config: dict) -> dict:
    """
    Analyze scraped posts.

    Returns summary statistics and insights.
    """
    companies = config.get("keywords", {}).get("companies", [])

    # Basic stats
    stats = {
        "total_posts": len(df),
        "date_range": {
            "start": df["created_utc"].min(),
            "end": df["created_utc"].max(),
        },
        "avg_score": df["score"].mean(),
        "avg_comments": df["num_comments"].mean(),
        "subreddit_breakdown": df["subreddit"].value_counts().to_dict(),
    }

    # Company mentions
    company_mentions = Counter()
    for _, row in df.iterrows():
        text = f"{row['title']} {row.get('selftext', '')}"
        found = extract_companies(text, companies)
        company_mentions.update(found)

    stats["company_mentions"] = dict(company_mentions.most_common(20))

    # Posts by day
    df["date"] = pd.to_datetime(df["created_utc"]).dt.date
    stats["posts_by_day"] = df.groupby("date").size().to_dict()

    # Top posts by engagement
    top_posts = df.nlargest(10, "score")[["title", "score", "num_comments", "subreddit"]]
    stats["top_posts"] = top_posts.to_dict("records")

    return stats


def print_analysis(stats: dict) -> None:
    """Print formatted analysis results."""
    print("\n" + "=" * 60)
    print("LAYOFF DATA ANALYSIS")
    print("=" * 60)

    print(f"\nTotal Posts: {stats['total_posts']}")
    print(f"Date Range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    print(f"Avg Score: {stats['avg_score']:.1f}")
    print(f"Avg Comments: {stats['avg_comments']:.1f}")

    print("\n--- Subreddit Breakdown ---")
    for sub, count in stats["subreddit_breakdown"].items():
        print(f"  r/{sub}: {count} posts")

    print("\n--- Top Company Mentions ---")
    for company, count in list(stats["company_mentions"].items())[:10]:
        print(f"  {company}: {count}")

    print("\n--- Top Posts by Score ---")
    for i, post in enumerate(stats["top_posts"][:5], 1):
        title = post["title"][:60] + "..." if len(post["title"]) > 60 else post["title"]
        print(f"  {i}. [{post['score']}] {title}")

    print("\n" + "=" * 60)
