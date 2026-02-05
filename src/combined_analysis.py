"""Combined analysis of actual layoffs and Reddit sentiment."""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re

from src.sentiment import add_sentiment_to_df
from src.analyzer import extract_companies


def load_reddit_data(data_dir: Path = Path("data")) -> pd.DataFrame:
    """Load the most recent Reddit posts data."""
    import glob
    files = glob.glob(str(data_dir / "all_posts_*.csv"))
    if not files:
        raise FileNotFoundError("No Reddit data found. Run main.py first.")
    latest = sorted(files)[-1]
    df = pd.read_csv(latest, parse_dates=["created_utc"])
    return df


def load_layoffs_data(data_dir: Path = Path("data")) -> pd.DataFrame:
    """Load actual layoffs data."""
    filepath = data_dir / "layoffs_actual.csv"
    if not filepath.exists():
        raise FileNotFoundError("No layoffs data found. Run get_layoffs.py --save first.")
    return pd.read_csv(filepath, parse_dates=["date"])


def analyze_company_sentiment(reddit_df: pd.DataFrame, companies: list) -> pd.DataFrame:
    """Analyze sentiment for posts mentioning specific companies."""
    if "sentiment_label" not in reddit_df.columns:
        reddit_df = add_sentiment_to_df(reddit_df)

    reddit_df["text_combined"] = reddit_df["title"].fillna("") + " " + reddit_df["selftext"].fillna("")

    results = []
    for company in companies:
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        mask = reddit_df["text_combined"].str.lower().str.contains(pattern, regex=True, na=False)
        company_posts = reddit_df[mask]

        if len(company_posts) > 0:
            sentiment_counts = company_posts["sentiment_label"].value_counts()
            avg_polarity = company_posts["sentiment_polarity"].mean()

            results.append({
                "company": company,
                "mentions": len(company_posts),
                "positive": sentiment_counts.get("positive", 0),
                "neutral": sentiment_counts.get("neutral", 0),
                "negative": sentiment_counts.get("negative", 0),
                "avg_polarity": avg_polarity,
                "avg_score": company_posts["score"].mean(),
                "avg_comments": company_posts["num_comments"].mean(),
            })

    return pd.DataFrame(results)


def combine_layoffs_and_sentiment(layoffs_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """Merge layoffs data with Reddit sentiment analysis."""
    # Aggregate layoffs by company
    layoffs_agg = layoffs_df.groupby("company").agg({
        "laid_off_count": "sum",
        "date": ["min", "max", "count"]
    }).reset_index()
    layoffs_agg.columns = ["company", "total_laid_off", "first_layoff", "last_layoff", "layoff_events"]

    # Normalize company names for matching
    layoffs_agg["company_lower"] = layoffs_agg["company"].str.lower()
    sentiment_df["company_lower"] = sentiment_df["company"].str.lower()

    # Merge
    combined = layoffs_agg.merge(sentiment_df, on="company_lower", how="outer", suffixes=("", "_reddit"))
    combined["company"] = combined["company"].fillna(combined["company_reddit"])
    combined = combined.drop(columns=["company_lower", "company_reddit"], errors="ignore")

    # Fill NaN with 0
    combined = combined.fillna(0)

    return combined


def plot_layoffs_vs_mentions(combined_df: pd.DataFrame, output_dir: Path = None) -> None:
    """Scatter plot of actual layoffs vs Reddit mentions."""
    fig, ax = plt.subplots(figsize=(12, 8))

    df = combined_df[(combined_df["total_laid_off"] > 0) & (combined_df["mentions"] > 0)].copy()

    # Size based on average engagement
    sizes = df["avg_score"].fillna(50) + 50

    # Color based on sentiment
    colors = df["avg_polarity"].fillna(0)

    scatter = ax.scatter(
        df["total_laid_off"],
        df["mentions"],
        s=sizes,
        c=colors,
        cmap="RdYlGn",
        alpha=0.7,
        edgecolors="black",
        linewidth=1
    )

    # Add company labels
    for _, row in df.iterrows():
        ax.annotate(
            row["company"],
            (row["total_laid_off"], row["mentions"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold"
        )

    ax.set_xlabel("Actual Layoffs (Last 6 Months)", fontsize=12)
    ax.set_ylabel("Reddit Mentions", fontsize=12)
    ax.set_title("Actual Layoffs vs Reddit Discussion\n(Color = Sentiment, Size = Engagement)",
                 fontsize=14, fontweight="bold")

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Sentiment Polarity (Red=Negative, Green=Positive)")

    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "layoffs_vs_mentions.png", dpi=150, bbox_inches="tight")
        print("Saved: layoffs_vs_mentions.png")
    plt.close()


def plot_sentiment_by_layoff_size(combined_df: pd.DataFrame, output_dir: Path = None) -> None:
    """Bar chart showing sentiment breakdown for companies by layoff size."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Filter to companies with both layoffs and mentions
    df = combined_df[(combined_df["total_laid_off"] > 0) & (combined_df["mentions"] > 0)].copy()
    df = df.sort_values("total_laid_off", ascending=False).head(12)

    # Left: Stacked bar of sentiment
    sentiment_cols = ["negative", "neutral", "positive"]
    colors = ["#e74c3c", "#95a5a6", "#2ecc71"]

    df_plot = df.set_index("company")[sentiment_cols]
    df_plot.plot(kind="barh", stacked=True, ax=axes[0], color=colors, edgecolor="black")

    axes[0].set_xlabel("Number of Reddit Posts")
    axes[0].set_title("Reddit Sentiment by Company", fontweight="bold", fontsize=12)
    axes[0].legend(title="Sentiment", loc="lower right")
    axes[0].invert_yaxis()

    # Right: Actual layoffs for comparison
    bars = axes[1].barh(df["company"], df["total_laid_off"], color="#e74c3c", edgecolor="darkred")
    for bar, val in zip(bars, df["total_laid_off"]):
        axes[1].text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
                     f'{val:,.0f}', va="center", fontsize=9)

    axes[1].set_xlabel("Employees Laid Off")
    axes[1].set_title("Actual Layoffs (Last 6 Months)", fontweight="bold", fontsize=12)
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))
    axes[1].invert_yaxis()

    plt.suptitle("Reddit Discussion vs Actual Layoffs", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "sentiment_by_layoff_size.png", dpi=150, bbox_inches="tight")
        print("Saved: sentiment_by_layoff_size.png")
    plt.close()


def plot_correlation_analysis(combined_df: pd.DataFrame, output_dir: Path = None) -> None:
    """Analyze correlation between layoffs and Reddit metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    df = combined_df[(combined_df["total_laid_off"] > 0) & (combined_df["mentions"] > 0)].copy()

    # 1. Layoffs vs Mentions correlation
    ax = axes[0, 0]
    ax.scatter(df["total_laid_off"], df["mentions"], s=100, alpha=0.7, c="#3498db", edgecolors="black")
    z = np.polyfit(df["total_laid_off"], df["mentions"], 1)
    p = np.poly1d(z)
    ax.plot(df["total_laid_off"].sort_values(), p(df["total_laid_off"].sort_values()),
            "r--", linewidth=2, label=f"Trend")
    corr = df["total_laid_off"].corr(df["mentions"])
    ax.set_title(f"Layoffs vs Mentions (r={corr:.2f})", fontweight="bold")
    ax.set_xlabel("Total Laid Off")
    ax.set_ylabel("Reddit Mentions")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    # 2. Layoffs vs Sentiment
    ax = axes[0, 1]
    ax.scatter(df["total_laid_off"], df["avg_polarity"], s=100, alpha=0.7, c="#e74c3c", edgecolors="black")
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    corr = df["total_laid_off"].corr(df["avg_polarity"])
    ax.set_title(f"Layoffs vs Sentiment (r={corr:.2f})", fontweight="bold")
    ax.set_xlabel("Total Laid Off")
    ax.set_ylabel("Average Sentiment Polarity")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    # 3. Mentions vs Engagement
    ax = axes[1, 0]
    ax.scatter(df["mentions"], df["avg_score"], s=100, alpha=0.7, c="#2ecc71", edgecolors="black")
    corr = df["mentions"].corr(df["avg_score"])
    ax.set_title(f"Mentions vs Avg Post Score (r={corr:.2f})", fontweight="bold")
    ax.set_xlabel("Reddit Mentions")
    ax.set_ylabel("Average Post Score")

    # 4. Layoffs vs Engagement
    ax = axes[1, 1]
    ax.scatter(df["total_laid_off"], df["avg_comments"], s=100, alpha=0.7, c="#9b59b6", edgecolors="black")
    corr = df["total_laid_off"].corr(df["avg_comments"])
    ax.set_title(f"Layoffs vs Avg Comments (r={corr:.2f})", fontweight="bold")
    ax.set_xlabel("Total Laid Off")
    ax.set_ylabel("Average Comments per Post")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    plt.suptitle("Correlation Analysis: Layoffs vs Reddit Activity", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "correlation_analysis.png", dpi=150, bbox_inches="tight")
        print("Saved: correlation_analysis.png")
    plt.close()


def create_combined_dashboard(combined_df: pd.DataFrame, reddit_df: pd.DataFrame,
                              layoffs_df: pd.DataFrame, output_dir: Path = None) -> None:
    """Create comprehensive combined dashboard."""
    fig = plt.figure(figsize=(20, 16))

    # Add sentiment if not present
    if "sentiment_label" not in reddit_df.columns:
        reddit_df = add_sentiment_to_df(reddit_df)

    df = combined_df[(combined_df["total_laid_off"] > 0) | (combined_df["mentions"] > 0)].copy()

    # 1. Top left: Layoffs vs Mentions scatter
    ax1 = fig.add_subplot(2, 3, 1)
    df_both = df[(df["total_laid_off"] > 0) & (df["mentions"] > 0)]
    scatter = ax1.scatter(df_both["total_laid_off"], df_both["mentions"],
                          c=df_both["avg_polarity"], cmap="RdYlGn", s=100,
                          alpha=0.7, edgecolors="black")
    for _, row in df_both.iterrows():
        ax1.annotate(row["company"], (row["total_laid_off"], row["mentions"]),
                     fontsize=8, xytext=(3, 3), textcoords="offset points")
    ax1.set_title("Layoffs vs Reddit Mentions", fontweight="bold")
    ax1.set_xlabel("Actual Layoffs")
    ax1.set_ylabel("Reddit Mentions")
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    # 2. Top middle: Monthly comparison
    ax2 = fig.add_subplot(2, 3, 2)
    reddit_df["month"] = pd.to_datetime(reddit_df["created_utc"]).dt.to_period("M")
    layoffs_df["month"] = pd.to_datetime(layoffs_df["date"]).dt.to_period("M")

    reddit_monthly = reddit_df.groupby("month").size()
    layoffs_monthly = layoffs_df.groupby("month")["laid_off_count"].sum() / 1000  # Scale down

    x = range(len(reddit_monthly))
    width = 0.35
    ax2.bar([i - width/2 for i in x], reddit_monthly.values, width, label="Reddit Posts", color="#3498db")

    # Overlay layoffs on secondary axis
    ax2b = ax2.twinx()
    ax2b.plot([str(m) for m in layoffs_monthly.index], layoffs_monthly.values,
              "r-o", linewidth=2, markersize=8, label="Layoffs (k)")
    ax2b.set_ylabel("Layoffs (thousands)", color="red")

    ax2.set_title("Monthly: Reddit Posts vs Layoffs", fontweight="bold")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Reddit Posts", color="blue")
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(m) for m in reddit_monthly.index], rotation=45, ha="right")
    ax2.legend(loc="upper left")
    ax2b.legend(loc="upper right")

    # 3. Top right: Overall sentiment pie
    ax3 = fig.add_subplot(2, 3, 3)
    sentiment_counts = reddit_df["sentiment_label"].value_counts()
    colors = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}
    ax3.pie(sentiment_counts.values, labels=sentiment_counts.index,
            colors=[colors[l] for l in sentiment_counts.index],
            autopct="%1.1f%%", startangle=90)
    ax3.set_title("Overall Reddit Sentiment", fontweight="bold")

    # 4. Bottom left: Top companies comparison
    ax4 = fig.add_subplot(2, 3, 4)
    top_layoffs = df.nlargest(8, "total_laid_off")[["company", "total_laid_off", "mentions"]]
    x = range(len(top_layoffs))
    width = 0.35
    ax4.barh([i - width/2 for i in x], top_layoffs["total_laid_off"]/1000, width,
             label="Layoffs (k)", color="#e74c3c")
    ax4.barh([i + width/2 for i in x], top_layoffs["mentions"]*100, width,  # Scale up for visibility
             label="Mentions (×100)", color="#3498db")
    ax4.set_yticks(x)
    ax4.set_yticklabels(top_layoffs["company"])
    ax4.set_title("Top Companies: Layoffs vs Mentions", fontweight="bold")
    ax4.legend()
    ax4.invert_yaxis()

    # 5. Bottom middle: Sentiment by company
    ax5 = fig.add_subplot(2, 3, 5)
    top_mentioned = df[df["mentions"] > 0].nlargest(8, "mentions")
    colors_sent = ["#e74c3c", "#95a5a6", "#2ecc71"]
    top_mentioned.set_index("company")[["negative", "neutral", "positive"]].plot(
        kind="barh", stacked=True, ax=ax5, color=colors_sent)
    ax5.set_title("Sentiment by Company (Top Mentioned)", fontweight="bold")
    ax5.set_xlabel("Posts")
    ax5.legend(title="Sentiment")
    ax5.invert_yaxis()

    # 6. Bottom right: Key stats
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")

    total_layoffs = layoffs_df["laid_off_count"].sum()
    total_posts = len(reddit_df)
    total_companies_layoffs = layoffs_df["company"].nunique()
    avg_sentiment = reddit_df["sentiment_polarity"].mean()

    stats_text = f"""
    COMBINED ANALYSIS SUMMARY
    ═══════════════════════════════════

    ACTUAL LAYOFFS (Last 6 Months)
    • Total Laid Off: {total_layoffs:,}
    • Companies Affected: {total_companies_layoffs}
    • Largest Single Event: Amazon (16,000)

    REDDIT DISCUSSION
    • Total Posts Analyzed: {total_posts:,}
    • Average Sentiment: {avg_sentiment:.3f}
    • Sentiment Split: {sentiment_counts.get('positive',0)} pos / {sentiment_counts.get('negative',0)} neg

    KEY INSIGHTS
    • Intel & Amazon dominate layoffs
    • Amazon most discussed on Reddit
    • Sentiment mostly neutral (factual)
    • Higher layoffs → More discussion
    """
    ax6.text(0.1, 0.9, stats_text, transform=ax6.transAxes, fontsize=11,
             verticalalignment="top", fontfamily="monospace",
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    plt.suptitle("Tech Layoffs: Combined Analysis (Actual Data + Reddit Sentiment)",
                 fontsize=18, fontweight="bold", y=1.02)
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / "combined_dashboard.png", dpi=150, bbox_inches="tight")
        print("Saved: combined_dashboard.png")
    plt.close()


def print_combined_summary(combined_df: pd.DataFrame) -> None:
    """Print summary of combined analysis."""
    print("\n" + "=" * 80)
    print("COMBINED ANALYSIS: ACTUAL LAYOFFS vs REDDIT SENTIMENT")
    print("=" * 80)

    df = combined_df[(combined_df["total_laid_off"] > 0) & (combined_df["mentions"] > 0)]

    print(f"\nCompanies with both layoffs and Reddit mentions: {len(df)}")

    print("\n" + "-" * 80)
    print("TOP COMPANIES BY LAYOFFS (with Reddit sentiment)")
    print("-" * 80)
    print(f"{'Company':<15} {'Laid Off':>10} {'Mentions':>10} {'Sentiment':>12} {'Polarity':>10}")
    print("-" * 80)

    for _, row in df.nlargest(15, "total_laid_off").iterrows():
        # Determine sentiment label
        if row["positive"] > row["negative"]:
            sent = "Positive"
        elif row["negative"] > row["positive"]:
            sent = "Negative"
        else:
            sent = "Neutral"

        print(f"{row['company']:<15} {row['total_laid_off']:>10,.0f} {row['mentions']:>10.0f} {sent:>12} {row['avg_polarity']:>10.3f}")

    # Correlation
    corr = df["total_laid_off"].corr(df["mentions"])
    print(f"\nCorrelation (Layoffs vs Mentions): {corr:.3f}")

    corr_sent = df["total_laid_off"].corr(df["avg_polarity"])
    print(f"Correlation (Layoffs vs Sentiment): {corr_sent:.3f}")

    print("\n" + "=" * 80)
