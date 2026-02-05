"""Data storage utilities."""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd


def save_posts_csv(posts: list[dict], filepath: Path) -> None:
    """Save posts to CSV file."""
    df = pd.DataFrame(posts)
    df.to_csv(filepath, index=False)
    print(f"Saved {len(posts)} posts to {filepath}")


def save_posts_json(posts: list[dict], filepath: Path) -> None:
    """Save posts to JSON file."""
    # Convert datetime objects to strings
    for post in posts:
        if isinstance(post.get("created_utc"), datetime):
            post["created_utc"] = post["created_utc"].isoformat()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(posts)} posts to {filepath}")


def load_posts_csv(filepath: Path) -> pd.DataFrame:
    """Load posts from CSV file."""
    return pd.read_csv(filepath, parse_dates=["created_utc"])


def load_posts_json(filepath: Path) -> list[dict]:
    """Load posts from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_output_path(data_dir: str, subreddit: str, data_type: str, ext: str) -> Path:
    """Generate timestamped output path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{subreddit}_{data_type}_{timestamp}.{ext}"
    path = Path(data_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
