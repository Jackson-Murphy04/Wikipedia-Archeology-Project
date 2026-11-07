from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
df = pd.read_csv(
    BASE / "cleaned/historical_revisions_cleaned.csv",
    parse_dates=["timestamp"]
)

FIGURES = BASE / "figures"
FIGURES.mkdir(exist_ok=True)

# 1. Monthly edit frequency
monthly = (
    df.groupby(["article_title", "month"])
    .size()
    .reset_index(name="revision_count")
)

monthly.to_csv(
    BASE / "cleaned/monthly_activity.csv",
    index=False
)

# Plot each article's monthly activity
pivot = monthly.pivot(
    index="month",
    columns="article_title",
    values="revision_count"
).fillna(0)

pivot.plot(figsize=(13, 6))
plt.title("Wikipedia Revision Activity by Article")
plt.xlabel("Month")
plt.ylabel("Revisions in Collected Sample")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(FIGURES / "monthly_activity.png", dpi=160)
plt.close()

# 2. Article size over time
plt.figure(figsize=(12, 6))

for article, group in df.groupby("article_title"):
    plt.plot(
        group["timestamp"],
        group["article_size_bytes"],
        label=article
    )

plt.title("Article Size Over Time")
plt.xlabel("Revision Date")
plt.ylabel("Article Size (Bytes)")
plt.legend()
plt.tight_layout()
plt.savefig(FIGURES / "article_growth.png", dpi=160)
plt.close()

# 3. Largest observed size differences
changes = df.dropna(
    subset=["sampled_size_change"]
).copy()

changes["absolute_change"] = (
    changes["sampled_size_change"].abs()
)

largest = changes.nlargest(20, "absolute_change")

largest[[
    "article_title",
    "revision_id",
    "timestamp",
    "sampled_size_change"
]].to_csv(
    BASE / "cleaned/largest_observed_changes.csv",
    index=False
)

print("Analysis complete.")
print("Figures saved in:", FIGURES)
