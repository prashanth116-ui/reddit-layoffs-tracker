"""Sentiment analysis for Reddit posts."""

from textblob import TextBlob
import pandas as pd


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of text using TextBlob.

    Returns:
        dict with polarity (-1 to 1) and subjectivity (0 to 1)
    """
    if not text or pd.isna(text):
        return {"polarity": 0, "subjectivity": 0, "label": "neutral"}

    blob = TextBlob(str(text))
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # Classify sentiment
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {
        "polarity": polarity,
        "subjectivity": subjectivity,
        "label": label,
    }


def add_sentiment_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """Add sentiment columns to dataframe."""
    df = df.copy()

    # Combine title and selftext for analysis
    df["text_combined"] = df["title"].fillna("") + " " + df["selftext"].fillna("")

    # Analyze sentiment
    print("Analyzing sentiment...")
    sentiments = df["text_combined"].apply(analyze_sentiment)

    df["sentiment_polarity"] = sentiments.apply(lambda x: x["polarity"])
    df["sentiment_subjectivity"] = sentiments.apply(lambda x: x["subjectivity"])
    df["sentiment_label"] = sentiments.apply(lambda x: x["label"])

    # Clean up
    df.drop(columns=["text_combined"], inplace=True)

    return df


def get_sentiment_summary(df: pd.DataFrame) -> dict:
    """Get sentiment summary statistics."""
    if "sentiment_label" not in df.columns:
        df = add_sentiment_to_df(df)

    total = len(df)
    label_counts = df["sentiment_label"].value_counts()

    summary = {
        "total_posts": total,
        "positive": label_counts.get("positive", 0),
        "negative": label_counts.get("negative", 0),
        "neutral": label_counts.get("neutral", 0),
        "positive_pct": label_counts.get("positive", 0) / total * 100,
        "negative_pct": label_counts.get("negative", 0) / total * 100,
        "neutral_pct": label_counts.get("neutral", 0) / total * 100,
        "avg_polarity": df["sentiment_polarity"].mean(),
        "avg_subjectivity": df["sentiment_subjectivity"].mean(),
    }

    # By subreddit
    summary["by_subreddit"] = {}
    for sub in df["subreddit"].unique():
        sub_df = df[df["subreddit"] == sub]
        sub_counts = sub_df["sentiment_label"].value_counts()
        summary["by_subreddit"][sub] = {
            "positive_pct": sub_counts.get("positive", 0) / len(sub_df) * 100,
            "negative_pct": sub_counts.get("negative", 0) / len(sub_df) * 100,
            "neutral_pct": sub_counts.get("neutral", 0) / len(sub_df) * 100,
            "avg_polarity": sub_df["sentiment_polarity"].mean(),
        }

    return summary


def print_sentiment_summary(summary: dict) -> None:
    """Print formatted sentiment summary."""
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS")
    print("=" * 60)

    print(f"\nOverall Distribution:")
    print(f"  Positive: {summary['positive']} ({summary['positive_pct']:.1f}%)")
    print(f"  Neutral:  {summary['neutral']} ({summary['neutral_pct']:.1f}%)")
    print(f"  Negative: {summary['negative']} ({summary['negative_pct']:.1f}%)")

    print(f"\nAverage Polarity: {summary['avg_polarity']:.3f} (-1=negative, +1=positive)")
    print(f"Average Subjectivity: {summary['avg_subjectivity']:.3f} (0=objective, 1=subjective)")

    print("\nBy Subreddit:")
    for sub, stats in summary["by_subreddit"].items():
        print(f"\n  r/{sub}:")
        print(f"    Positive: {stats['positive_pct']:.1f}%")
        print(f"    Negative: {stats['negative_pct']:.1f}%")
        print(f"    Avg Polarity: {stats['avg_polarity']:.3f}")

    print("\n" + "=" * 60)
