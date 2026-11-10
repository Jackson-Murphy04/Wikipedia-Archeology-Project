"""Shared, reproducible helpers for the Wikipedia revision analysis notebooks."""
from pathlib import Path
import re
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "historical_analysis" / "cleaned" / "historical_revisions_cleaned.csv"
OUTPUT_DIR = PROJECT_ROOT / "analysis" / "analysis_results"
FIGURES_DIR = PROJECT_ROOT / "analysis" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLUMNS = ["article_title", "revision_id", "parent_id", "timestamp", "username",
                    "user_id", "edit_comment", "article_size_bytes", "is_minor"]


def load_revisions():
    """Load and normalize revision metadata; preserve raw identity fields."""
    df = pd.read_csv(DATA_PATH, low_memory=False)
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for col in ["revision_id", "parent_id", "user_id", "article_size_bytes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["username_missing"] = df["username"].isna() | df["username"].astype("string").str.strip().eq("")
    df["comment_missing"] = df["edit_comment"].isna() | df["edit_comment"].astype("string").str.strip().eq("")
    df["username"] = df["username"].astype("string").str.strip().mask(lambda s: s.eq(""))
    df["edit_comment"] = df["edit_comment"].fillna("").astype(str)
    df["is_minor"] = (df["is_minor"].astype(str).str.lower()
                       .isin(["true", "1", "yes"]))
    df["year"] = df["timestamp"].dt.year
    df = df.sort_values(["article_title", "timestamp", "revision_id"], na_position="last").reset_index(drop=True)
    df["size_change_bytes"] = df.groupby("article_title", sort=False)["article_size_bytes"].diff()
    return df


def finish_plot(fig, filename):
    """Save a PNG and display the same figure in notebook output."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=220, bbox_inches="tight")
    plt.show()
    plt.close(fig)


def save_table(df, filename):
    path = OUTPUT_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def category_map():
    """Documented primary category mapping for the 31 collected article titles."""
    groups = {
        "Wars and military conflicts": ["American Civil War", "Battle of Gettysburg", "Cold War", "Gulf War", "Korean War", "Vietnam War", "World War I", "World War II"],
        "Political events and scandals": ["Assassination of John F. Kennedy", "Cuban Missile Crisis", "Watergate scandal"],
        "Natural and technological disasters": ["Atomic bombings of Hiroshima and Nagasaki", "Black Death", "Great Fire of London", "Sinking of the Titanic", "September 11 attacks"],
        "Revolutions and independence movements": ["American Revolution", "Arab Spring", "Boston Tea Party", "Chinese Revolution", "Fall of the Berlin Wall", "Haitian Revolution", "Iranian Revolution", "Mexican Revolution", "Partition of India", "Russian Revolution"],
        "Social movements and civil rights": ["Emancipation Proclamation", "Cultural Revolution"],
        "Other historical developments": ["Great Depression", "Magna Carta", "Renaissance"],
    }
    return {article: group for group, articles in groups.items() for article in articles}


def monthly_activity(df):
    valid = df.dropna(subset=["timestamp"])
    return (valid.set_index("timestamp").groupby("article_title").resample("MS")
            .size().rename("revisions").reset_index())


def robust_spikes(activity):
    """Flag article-month outliers; fall back to Tukey fences when MAD is zero."""
    out = activity.copy()
    stats = out.groupby("article_title")["revisions"].agg(
        article_median="median",
        mad=lambda x: float(np.median(np.abs(x - np.median(x)))),
        q1=lambda x: float(x.quantile(0.25)),
        q3=lambda x: float(x.quantile(0.75)),
    )
    stats["scaled_mad_threshold"] = stats.article_median + 3 * 1.4826 * stats.mad
    stats["iqr_threshold"] = stats.q3 + 1.5 * (stats.q3 - stats.q1)
    stats["robust_threshold"] = np.where(
        stats.mad > 0,
        stats.scaled_mad_threshold,
        np.where(stats.q3 > stats.q1, stats.iqr_threshold, np.inf),
    )
    out = out.merge(stats[["article_median", "robust_threshold"]], left_on="article_title", right_index=True)
    out["is_spike"] = out["revisions"] > out["robust_threshold"]
    return out


def classify_editors(df):
    """Use user_id=0 as anonymous, positive IDs as registered, missing as unknown."""
    result = df.copy()
    result["editor_type"] = np.select(
        [result["user_id"].eq(0), result["user_id"].gt(0)],
        ["Anonymous (user ID 0)", "Registered (positive user ID)"],
        default="Unknown / unavailable")
    return result


def gini(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0 or np.all(x == 0):
        return 0.0
    x = np.sort(np.maximum(x, 0))
    n = len(x)
    return float((2 * np.sum((np.arange(1, n + 1)) * x) / (n * x.sum())) - (n + 1) / n)

