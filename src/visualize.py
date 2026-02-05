"""Visualization utilities for layoff data."""

from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.sentiment import add_sentiment_to_df

# Set style
sns.set_theme(style="darkgrid")
plt.rcParams["figure.figsize"] = (12, 6)


def plot_posts_over_time(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot number of posts per day."""
    fig, ax = plt.subplots(figsize=(14, 5))

    df["date"] = pd.to_datetime(df["created_utc"]).dt.date
    daily = df.groupby(["date", "subreddit"]).size().unstack(fill_value=0)

    daily.plot(kind="bar", stacked=True, ax=ax, width=0.8, color=["#FF4500", "#1E90FF"])

    ax.set_title("Posts Per Day by Subreddit", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Posts")
    ax.legend(title="Subreddit", labels=[f"r/{c}" for c in daily.columns])

    # Rotate x labels
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "posts_over_time.png", dpi=150)
        print(f"Saved: posts_over_time.png")
    plt.show()


def plot_company_mentions(stats: dict, output_dir: Path = None) -> None:
    """Plot top company mentions as horizontal bar chart."""
    fig, ax = plt.subplots(figsize=(10, 6))

    companies = stats.get("company_mentions", {})
    if not companies:
        print("No company mentions to plot")
        return

    # Top 15 companies
    top = dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:15])

    colors = sns.color_palette("Oranges_r", len(top))
    bars = ax.barh(list(top.keys())[::-1], list(top.values())[::-1], color=colors)

    ax.set_title("Top Company Mentions in Layoff Posts", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Mentions")

    # Add count labels
    for bar, count in zip(bars, list(top.values())[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                str(count), va="center", fontsize=10)

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "company_mentions.png", dpi=150)
        print(f"Saved: company_mentions.png")
    plt.show()


def plot_score_distribution(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot distribution of post scores."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    for sub in df["subreddit"].unique():
        subset = df[df["subreddit"] == sub]["score"]
        # Cap at 500 for better visualization
        subset_capped = subset.clip(upper=500)
        axes[0].hist(subset_capped, bins=50, alpha=0.6, label=f"r/{sub}")

    axes[0].set_title("Score Distribution (capped at 500)", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Score")
    axes[0].set_ylabel("Count")
    axes[0].legend()

    # Box plot by subreddit
    df_plot = df.copy()
    df_plot["score_capped"] = df_plot["score"].clip(upper=500)
    sns.boxplot(data=df_plot, x="subreddit", y="score_capped", ax=axes[1], palette="Set2")
    axes[1].set_title("Score by Subreddit", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Subreddit")
    axes[1].set_ylabel("Score")

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "score_distribution.png", dpi=150)
        print(f"Saved: score_distribution.png")
    plt.show()


def plot_engagement_scatter(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Scatter plot of score vs comments."""
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {"layoffs": "#FF4500", "jobs": "#1E90FF"}

    for sub in df["subreddit"].unique():
        subset = df[df["subreddit"] == sub]
        ax.scatter(
            subset["score"].clip(upper=2000),
            subset["num_comments"].clip(upper=300),
            alpha=0.5,
            label=f"r/{sub}",
            c=colors.get(sub, "gray"),
            s=30,
        )

    ax.set_title("Post Engagement: Score vs Comments", fontsize=14, fontweight="bold")
    ax.set_xlabel("Score (capped at 2000)")
    ax.set_ylabel("Number of Comments (capped at 300)")
    ax.legend()

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "engagement_scatter.png", dpi=150)
        print(f"Saved: engagement_scatter.png")
    plt.show()


def plot_weekly_trend(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot weekly post volume trend."""
    fig, ax = plt.subplots(figsize=(12, 5))

    df["week"] = pd.to_datetime(df["created_utc"]).dt.to_period("W").dt.start_time
    weekly = df.groupby(["week", "subreddit"]).size().unstack(fill_value=0)

    weekly.plot(kind="line", marker="o", ax=ax, linewidth=2, markersize=6)

    ax.set_title("Weekly Post Trend", fontsize=14, fontweight="bold")
    ax.set_xlabel("Week")
    ax.set_ylabel("Number of Posts")
    ax.legend(title="Subreddit", labels=[f"r/{c}" for c in weekly.columns])

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "weekly_trend.png", dpi=150)
        print(f"Saved: weekly_trend.png")
    plt.show()


def plot_top_posts(df: pd.DataFrame, n: int = 10, output_dir: Path = None) -> None:
    """Plot top posts by score."""
    fig, ax = plt.subplots(figsize=(12, 6))

    top = df.nlargest(n, "score")[["title", "score", "subreddit"]].copy()
    top["title_short"] = top["title"].str[:50] + "..."
    top = top.iloc[::-1]  # Reverse for horizontal bar

    colors = ["#FF4500" if s == "layoffs" else "#1E90FF" for s in top["subreddit"]]
    bars = ax.barh(range(len(top)), top["score"], color=colors)

    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["title_short"])
    ax.set_title(f"Top {n} Posts by Score", fontsize=14, fontweight="bold")
    ax.set_xlabel("Score")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#FF4500", label="r/layoffs"),
        Patch(facecolor="#1E90FF", label="r/jobs"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "top_posts.png", dpi=150)
        print(f"Saved: top_posts.png")
    plt.show()


def create_dashboard(df: pd.DataFrame, stats: dict, output_dir: Path = None) -> None:
    """Create a multi-panel dashboard."""
    fig = plt.figure(figsize=(16, 12))

    # 1. Weekly trend (top left)
    ax1 = fig.add_subplot(2, 2, 1)
    df["week"] = pd.to_datetime(df["created_utc"]).dt.to_period("W").dt.start_time
    weekly = df.groupby(["week", "subreddit"]).size().unstack(fill_value=0)
    weekly.plot(kind="line", marker="o", ax=ax1, linewidth=2)
    ax1.set_title("Weekly Post Trend", fontweight="bold")
    ax1.set_xlabel("Week")
    ax1.set_ylabel("Posts")
    ax1.legend([f"r/{c}" for c in weekly.columns])
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 2. Company mentions (top right)
    ax2 = fig.add_subplot(2, 2, 2)
    companies = stats.get("company_mentions", {})
    top = dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10])
    if top:
        ax2.barh(list(top.keys())[::-1], list(top.values())[::-1], color=sns.color_palette("Oranges_r", len(top)))
        ax2.set_title("Top Company Mentions", fontweight="bold")
        ax2.set_xlabel("Mentions")

    # 3. Score distribution (bottom left)
    ax3 = fig.add_subplot(2, 2, 3)
    for sub in df["subreddit"].unique():
        subset = df[df["subreddit"] == sub]["score"].clip(upper=500)
        ax3.hist(subset, bins=40, alpha=0.6, label=f"r/{sub}")
    ax3.set_title("Score Distribution", fontweight="bold")
    ax3.set_xlabel("Score")
    ax3.set_ylabel("Count")
    ax3.legend()

    # 4. Engagement scatter (bottom right)
    ax4 = fig.add_subplot(2, 2, 4)
    colors = {"layoffs": "#FF4500", "jobs": "#1E90FF"}
    for sub in df["subreddit"].unique():
        subset = df[df["subreddit"] == sub]
        ax4.scatter(
            subset["score"].clip(upper=1500),
            subset["num_comments"].clip(upper=200),
            alpha=0.5, label=f"r/{sub}", c=colors.get(sub, "gray"), s=20
        )
    ax4.set_title("Score vs Comments", fontweight="bold")
    ax4.set_xlabel("Score")
    ax4.set_ylabel("Comments")
    ax4.legend()

    plt.suptitle("Reddit Layoffs Dashboard", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "dashboard.png", dpi=150, bbox_inches="tight")
        print(f"Saved: dashboard.png")
    plt.show()


def plot_sentiment_distribution(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot sentiment distribution pie chart and bar chart."""
    if "sentiment_label" not in df.columns:
        df = add_sentiment_to_df(df)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Pie chart - overall
    colors = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}
    counts = df["sentiment_label"].value_counts()

    axes[0].pie(
        counts.values,
        labels=[f"{l.capitalize()}\n({v})" for l, v in counts.items()],
        colors=[colors[l] for l in counts.index],
        autopct="%1.1f%%",
        startangle=90,
        explode=[0.02] * len(counts),
    )
    axes[0].set_title("Overall Sentiment Distribution", fontsize=12, fontweight="bold")

    # Bar chart - by subreddit
    sentiment_by_sub = df.groupby(["subreddit", "sentiment_label"]).size().unstack(fill_value=0)
    sentiment_by_sub_pct = sentiment_by_sub.div(sentiment_by_sub.sum(axis=1), axis=0) * 100

    sentiment_by_sub_pct[["positive", "neutral", "negative"]].plot(
        kind="bar",
        ax=axes[1],
        color=[colors["positive"], colors["neutral"], colors["negative"]],
        width=0.7,
    )
    axes[1].set_title("Sentiment by Subreddit", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Subreddit")
    axes[1].set_ylabel("Percentage")
    axes[1].legend(title="Sentiment")
    axes[1].set_xticklabels([f"r/{x.get_text()}" for x in axes[1].get_xticklabels()], rotation=0)

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "sentiment_distribution.png", dpi=150)
        print(f"Saved: sentiment_distribution.png")
    plt.show()

    return df


def plot_sentiment_over_time(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot sentiment trend over time."""
    if "sentiment_label" not in df.columns:
        df = add_sentiment_to_df(df)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))

    df["date"] = pd.to_datetime(df["created_utc"]).dt.date

    # Daily average polarity
    daily_polarity = df.groupby("date")["sentiment_polarity"].mean()

    axes[0].plot(daily_polarity.index, daily_polarity.values, marker="o", linewidth=2, color="#3498db")
    axes[0].axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    axes[0].fill_between(
        daily_polarity.index,
        daily_polarity.values,
        0,
        where=(daily_polarity.values > 0),
        alpha=0.3,
        color="#2ecc71",
        label="Positive",
    )
    axes[0].fill_between(
        daily_polarity.index,
        daily_polarity.values,
        0,
        where=(daily_polarity.values < 0),
        alpha=0.3,
        color="#e74c3c",
        label="Negative",
    )
    axes[0].set_title("Daily Average Sentiment Polarity", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Date")
    axes[0].set_ylabel("Polarity (-1 to +1)")
    axes[0].legend()
    plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Daily sentiment counts
    daily_sentiment = df.groupby(["date", "sentiment_label"]).size().unstack(fill_value=0)
    colors = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}

    for label in ["positive", "neutral", "negative"]:
        if label in daily_sentiment.columns:
            axes[1].plot(
                daily_sentiment.index,
                daily_sentiment[label],
                marker="o",
                linewidth=2,
                label=label.capitalize(),
                color=colors[label],
            )

    axes[1].set_title("Daily Sentiment Counts", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Number of Posts")
    axes[1].legend()
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "sentiment_over_time.png", dpi=150)
        print(f"Saved: sentiment_over_time.png")
    plt.show()

    return df


def plot_sentiment_vs_engagement(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot relationship between sentiment and engagement."""
    if "sentiment_label" not in df.columns:
        df = add_sentiment_to_df(df)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    colors = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}

    # Scatter: polarity vs score
    for label in ["positive", "neutral", "negative"]:
        subset = df[df["sentiment_label"] == label]
        axes[0].scatter(
            subset["sentiment_polarity"],
            subset["score"].clip(upper=1000),
            alpha=0.5,
            label=label.capitalize(),
            c=colors[label],
            s=30,
        )

    axes[0].set_title("Sentiment vs Score", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Sentiment Polarity")
    axes[0].set_ylabel("Score (capped at 1000)")
    axes[0].legend()

    # Box plot: sentiment label vs score
    order = ["negative", "neutral", "positive"]
    sns.boxplot(
        data=df,
        x="sentiment_label",
        y=df["score"].clip(upper=500),
        order=order,
        palette=colors,
        ax=axes[1],
    )
    axes[1].set_title("Score Distribution by Sentiment", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Sentiment")
    axes[1].set_ylabel("Score (capped at 500)")

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "sentiment_vs_engagement.png", dpi=150)
        print(f"Saved: sentiment_vs_engagement.png")
    plt.show()

    return df


def create_sentiment_dashboard(df: pd.DataFrame, output_dir: Path = None) -> pd.DataFrame:
    """Create a sentiment-focused dashboard."""
    if "sentiment_label" not in df.columns:
        df = add_sentiment_to_df(df)

    fig = plt.figure(figsize=(16, 12))

    colors = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}

    # 1. Pie chart (top left)
    ax1 = fig.add_subplot(2, 2, 1)
    counts = df["sentiment_label"].value_counts()
    ax1.pie(
        counts.values,
        labels=[f"{l.capitalize()}" for l in counts.index],
        colors=[colors[l] for l in counts.index],
        autopct="%1.1f%%",
        startangle=90,
    )
    ax1.set_title("Overall Sentiment", fontweight="bold")

    # 2. By subreddit (top right)
    ax2 = fig.add_subplot(2, 2, 2)
    sentiment_by_sub = df.groupby(["subreddit", "sentiment_label"]).size().unstack(fill_value=0)
    sentiment_by_sub_pct = sentiment_by_sub.div(sentiment_by_sub.sum(axis=1), axis=0) * 100
    if all(c in sentiment_by_sub_pct.columns for c in ["positive", "neutral", "negative"]):
        sentiment_by_sub_pct[["positive", "neutral", "negative"]].plot(
            kind="bar", ax=ax2, color=[colors["positive"], colors["neutral"], colors["negative"]], width=0.7
        )
    ax2.set_title("Sentiment by Subreddit", fontweight="bold")
    ax2.set_ylabel("Percentage")
    ax2.set_xticklabels([f"r/{x.get_text()}" for x in ax2.get_xticklabels()], rotation=0)
    ax2.legend(title="Sentiment")

    # 3. Polarity over time (bottom left)
    ax3 = fig.add_subplot(2, 2, 3)
    df["date"] = pd.to_datetime(df["created_utc"]).dt.date
    daily_polarity = df.groupby("date")["sentiment_polarity"].mean()
    ax3.plot(daily_polarity.index, daily_polarity.values, marker="o", linewidth=2, color="#3498db")
    ax3.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax3.fill_between(daily_polarity.index, daily_polarity.values, 0,
                     where=(daily_polarity.values > 0), alpha=0.3, color="#2ecc71")
    ax3.fill_between(daily_polarity.index, daily_polarity.values, 0,
                     where=(daily_polarity.values < 0), alpha=0.3, color="#e74c3c")
    ax3.set_title("Daily Avg Polarity", fontweight="bold")
    ax3.set_ylabel("Polarity")
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 4. Sentiment vs score (bottom right)
    ax4 = fig.add_subplot(2, 2, 4)
    order = ["negative", "neutral", "positive"]
    sns.boxplot(data=df, x="sentiment_label", y=df["score"].clip(upper=500),
                order=order, palette=colors, ax=ax4)
    ax4.set_title("Score by Sentiment", fontweight="bold")
    ax4.set_xlabel("Sentiment")
    ax4.set_ylabel("Score")

    plt.suptitle("Sentiment Analysis Dashboard", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "sentiment_dashboard.png", dpi=150, bbox_inches="tight")
        print(f"Saved: sentiment_dashboard.png")
    plt.show()

    return df
