"""Visualization for actual layoff data."""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_theme(style="darkgrid")
plt.rcParams["figure.figsize"] = (12, 6)


def plot_monthly_trend(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot monthly layoff trend."""
    fig, ax = plt.subplots(figsize=(12, 6))

    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')['laid_off_count'].sum()

    # Convert period to timestamp for plotting
    x = [str(m) for m in monthly.index]
    y = monthly.values

    bars = ax.bar(x, y, color='#e74c3c', edgecolor='darkred', linewidth=1.5)

    # Add value labels on bars
    for bar, val in zip(bars, y):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                f'{val:,.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_title('Monthly Tech Layoffs (Last 6 Months)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Employees Laid Off', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    # Add trend line
    z = np.polyfit(range(len(y)), y, 1)
    p = np.poly1d(z)
    ax.plot(x, p(range(len(y))), "b--", alpha=0.7, linewidth=2, label='Trend')
    ax.legend()

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / 'layoffs_monthly_trend.png', dpi=150, bbox_inches='tight')
        print(f'Saved: layoffs_monthly_trend.png')
    plt.close()


def plot_top_companies(df: pd.DataFrame, top_n: int = 15, output_dir: Path = None) -> None:
    """Plot top companies by total layoffs."""
    fig, ax = plt.subplots(figsize=(12, 8))

    company_totals = df.groupby('company')['laid_off_count'].sum().sort_values(ascending=True).tail(top_n)

    colors = sns.color_palette('Reds_r', len(company_totals))
    bars = ax.barh(company_totals.index, company_totals.values, color=colors, edgecolor='darkred')

    # Add value labels
    for bar, val in zip(bars, company_totals.values):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
                f'{val:,.0f}', va='center', fontsize=10, fontweight='bold')

    ax.set_title(f'Top {top_n} Companies by Total Layoffs', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Total Employees Laid Off', fontsize=12)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / 'layoffs_top_companies.png', dpi=150, bbox_inches='tight')
        print(f'Saved: layoffs_top_companies.png')
    plt.close()


def plot_industry_breakdown(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Plot layoffs by industry."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    industry_totals = df.groupby('industry')['laid_off_count'].sum().sort_values(ascending=False)

    # Pie chart
    colors = sns.color_palette('Set2', len(industry_totals))
    wedges, texts, autotexts = axes[0].pie(
        industry_totals.values,
        labels=industry_totals.index,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 2 else '',
        colors=colors,
        explode=[0.05 if i == 0 else 0 for i in range(len(industry_totals))],
        startangle=90
    )
    axes[0].set_title('Layoffs by Industry', fontsize=14, fontweight='bold')

    # Bar chart
    bars = axes[1].barh(industry_totals.index[::-1], industry_totals.values[::-1], color=colors[::-1])
    for bar, val in zip(bars, industry_totals.values[::-1]):
        axes[1].text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                     f'{val:,.0f}', va='center', fontsize=10)
    axes[1].set_title('Layoffs by Industry (Count)', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Employees Laid Off')
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / 'layoffs_by_industry.png', dpi=150, bbox_inches='tight')
        print(f'Saved: layoffs_by_industry.png')
    plt.close()


def plot_company_timeline(df: pd.DataFrame, top_n: int = 10, output_dir: Path = None) -> None:
    """Plot timeline heatmap of layoffs by company."""
    fig, ax = plt.subplots(figsize=(14, 8))

    df['month'] = df['date'].dt.to_period('M')

    # Get top companies
    top_companies = df.groupby('company')['laid_off_count'].sum().nlargest(top_n).index

    # Create pivot table
    pivot = df[df['company'].isin(top_companies)].pivot_table(
        index='company',
        columns='month',
        values='laid_off_count',
        aggfunc='sum',
        fill_value=0
    )

    # Sort by total
    pivot['total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('total', ascending=False).drop('total', axis=1)

    # Create heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=',d',
        cmap='Reds',
        linewidths=0.5,
        ax=ax,
        cbar_kws={'label': 'Employees Laid Off'}
    )

    ax.set_title(f'Layoff Timeline - Top {top_n} Companies', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Company', fontsize=12)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / 'layoffs_timeline_heatmap.png', dpi=150, bbox_inches='tight')
        print(f'Saved: layoffs_timeline_heatmap.png')
    plt.close()


def plot_stacked_area(df: pd.DataFrame, top_n: int = 8, output_dir: Path = None) -> None:
    """Plot stacked area chart of layoffs over time."""
    fig, ax = plt.subplots(figsize=(14, 7))

    df['month'] = df['date'].dt.to_period('M')

    # Get top companies
    top_companies = df.groupby('company')['laid_off_count'].sum().nlargest(top_n).index.tolist()

    # Create pivot
    pivot = df.pivot_table(
        index='month',
        columns='company',
        values='laid_off_count',
        aggfunc='sum',
        fill_value=0
    )

    # Reorder columns by total
    company_order = df.groupby('company')['laid_off_count'].sum().sort_values(ascending=False).index
    pivot = pivot[[c for c in company_order if c in pivot.columns]]

    # Keep top N + "Others"
    if len(pivot.columns) > top_n:
        others = pivot.iloc[:, top_n:].sum(axis=1)
        pivot = pivot.iloc[:, :top_n]
        pivot['Others'] = others

    # Plot
    colors = sns.color_palette('tab10', len(pivot.columns))
    pivot.plot.area(ax=ax, stacked=True, color=colors, alpha=0.8)

    ax.set_title('Monthly Layoffs by Company (Stacked)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Employees Laid Off', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / 'layoffs_stacked_area.png', dpi=150, bbox_inches='tight')
        print(f'Saved: layoffs_stacked_area.png')
    plt.close()


def create_layoffs_dashboard(df: pd.DataFrame, output_dir: Path = None) -> None:
    """Create comprehensive layoffs dashboard."""
    fig = plt.figure(figsize=(18, 14))

    df['month'] = df['date'].dt.to_period('M')

    # 1. Monthly trend (top left)
    ax1 = fig.add_subplot(2, 2, 1)
    monthly = df.groupby('month')['laid_off_count'].sum()
    x = [str(m) for m in monthly.index]
    bars = ax1.bar(x, monthly.values, color='#e74c3c', edgecolor='darkred')
    for bar, val in zip(bars, monthly.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 300,
                 f'{val/1000:.1f}k', ha='center', fontsize=9, fontweight='bold')
    ax1.set_title('Monthly Layoffs', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Laid Off')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # 2. Top companies (top right)
    ax2 = fig.add_subplot(2, 2, 2)
    top_companies = df.groupby('company')['laid_off_count'].sum().nlargest(10)
    colors = sns.color_palette('Reds_r', len(top_companies))
    bars = ax2.barh(top_companies.index[::-1], top_companies.values[::-1], color=colors[::-1])
    for bar, val in zip(bars, top_companies.values[::-1]):
        ax2.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
                 f'{val:,.0f}', va='center', fontsize=9)
    ax2.set_title('Top 10 Companies', fontweight='bold', fontsize=12)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    # 3. Industry breakdown (bottom left)
    ax3 = fig.add_subplot(2, 2, 3)
    industry_totals = df.groupby('industry')['laid_off_count'].sum()
    colors = sns.color_palette('Set2', len(industry_totals))
    ax3.pie(industry_totals.values, labels=industry_totals.index,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
            colors=colors, startangle=90)
    ax3.set_title('By Industry', fontweight='bold', fontsize=12)

    # 4. Timeline heatmap (bottom right)
    ax4 = fig.add_subplot(2, 2, 4)
    top_co = df.groupby('company')['laid_off_count'].sum().nlargest(8).index
    pivot = df[df['company'].isin(top_co)].pivot_table(
        index='company', columns='month', values='laid_off_count', aggfunc='sum', fill_value=0
    )
    pivot = pivot.loc[top_co]  # Maintain order
    sns.heatmap(pivot, annot=True, fmt=',d', cmap='Reds', linewidths=0.5, ax=ax4,
                cbar_kws={'label': 'Laid Off'}, annot_kws={'size': 8})
    ax4.set_title('Timeline (Top 8)', fontweight='bold', fontsize=12)
    ax4.set_xlabel('')
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Main title
    total = df['laid_off_count'].sum()
    plt.suptitle(f'Tech Layoffs Dashboard - {total:,} Total Layoffs (Last 6 Months)',
                 fontsize=18, fontweight='bold', y=1.02)

    plt.tight_layout()

    if output_dir:
        plt.savefig(output_dir / 'layoffs_dashboard.png', dpi=150, bbox_inches='tight')
        print(f'Saved: layoffs_dashboard.png')
    plt.close()
