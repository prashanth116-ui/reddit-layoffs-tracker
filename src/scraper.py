"""Reddit scraper - supports both PRAW (authenticated) and public JSON API."""

import os
import time
from datetime import datetime
from typing import Generator

import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Public JSON API (no authentication required)
# ---------------------------------------------------------------------------

def scrape_subreddit_public(
    subreddit_name: str,
    limit: int = 500,
    sort_by: str = "new",
    time_filter: str = "month",
) -> Generator[dict, None, None]:
    """
    Scrape posts using Reddit's public JSON API (no auth required).

    Args:
        subreddit_name: Name of subreddit (without r/)
        limit: Max posts to fetch
        sort_by: new, hot, top, rising
        time_filter: hour, day, week, month, year, all (for top)

    Yields:
        Dict with post data
    """
    base_url = f"https://www.reddit.com/r/{subreddit_name}/{sort_by}.json"
    headers = {"User-Agent": "layoffs-tracker/1.0"}

    params = {"limit": min(limit, 100)}  # Reddit caps at 100 per request
    if sort_by == "top":
        params["t"] = time_filter

    after = None
    fetched = 0

    while fetched < limit:
        if after:
            params["after"] = after

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"  Error fetching data: {e}")
            break

        posts = data.get("data", {}).get("children", [])
        if not posts:
            break

        for post in posts:
            if fetched >= limit:
                break

            p = post["data"]
            yield {
                "id": p["id"],
                "subreddit": subreddit_name,
                "title": p["title"],
                "selftext": p.get("selftext", ""),
                "author": p.get("author", "[deleted]"),
                "created_utc": datetime.utcfromtimestamp(p["created_utc"]),
                "score": p["score"],
                "upvote_ratio": p.get("upvote_ratio", 0),
                "num_comments": p["num_comments"],
                "url": p["url"],
                "permalink": f"https://reddit.com{p['permalink']}",
                "is_self": p["is_self"],
                "flair": p.get("link_flair_text"),
            }
            fetched += 1

        after = data.get("data", {}).get("after")
        if not after:
            break

        # Rate limiting - be respectful
        time.sleep(1)


def scrape_comments_public(
    post_id: str,
    subreddit: str,
    limit: int = 50,
) -> Generator[dict, None, None]:
    """
    Scrape comments using Reddit's public JSON API.

    Args:
        post_id: Reddit post ID
        subreddit: Subreddit name
        limit: Max comments to fetch

    Yields:
        Dict with comment data
    """
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
    headers = {"User-Agent": "layoffs-tracker/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"  Error fetching comments: {e}")
        return

    if len(data) < 2:
        return

    comments_data = data[1].get("data", {}).get("children", [])
    count = 0

    def extract_comments(comments):
        nonlocal count
        for comment in comments:
            if count >= limit:
                return
            if comment["kind"] != "t1":  # Skip non-comment entries
                continue

            c = comment["data"]
            yield {
                "id": c["id"],
                "post_id": post_id,
                "body": c.get("body", ""),
                "author": c.get("author", "[deleted]"),
                "created_utc": datetime.utcfromtimestamp(c["created_utc"]) if c.get("created_utc") else None,
                "score": c.get("score", 0),
                "is_submitter": c.get("is_submitter", False),
                "parent_id": c.get("parent_id", ""),
            }
            count += 1

            # Handle nested replies
            replies = c.get("replies")
            if replies and isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                yield from extract_comments(reply_children)

    yield from extract_comments(comments_data)


# ---------------------------------------------------------------------------
# PRAW API (authenticated - optional)
# ---------------------------------------------------------------------------

def has_credentials() -> bool:
    """Check if Reddit API credentials are configured (not placeholders)."""
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    # Check they exist and aren't placeholder values
    placeholders = ["your_client_id_here", "your_client_secret_here", ""]
    return client_id not in placeholders and client_secret not in placeholders


def create_reddit_client():
    """Create authenticated Reddit client using PRAW."""
    import praw
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "layoffs-tracker/1.0"),
    )


def scrape_subreddit_praw(
    reddit,
    subreddit_name: str,
    limit: int = 500,
    sort_by: str = "new",
    time_filter: str = "month",
) -> Generator[dict, None, None]:
    """Scrape posts using PRAW (authenticated)."""
    subreddit = reddit.subreddit(subreddit_name)

    if sort_by == "new":
        posts = subreddit.new(limit=limit)
    elif sort_by == "hot":
        posts = subreddit.hot(limit=limit)
    elif sort_by == "top":
        posts = subreddit.top(time_filter=time_filter, limit=limit)
    elif sort_by == "rising":
        posts = subreddit.rising(limit=limit)
    else:
        posts = subreddit.new(limit=limit)

    for post in posts:
        yield {
            "id": post.id,
            "subreddit": subreddit_name,
            "title": post.title,
            "selftext": post.selftext,
            "author": str(post.author) if post.author else "[deleted]",
            "created_utc": datetime.utcfromtimestamp(post.created_utc),
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "url": post.url,
            "permalink": f"https://reddit.com{post.permalink}",
            "is_self": post.is_self,
            "flair": post.link_flair_text,
        }
