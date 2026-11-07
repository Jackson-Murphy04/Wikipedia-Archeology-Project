
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
INPUT = BASE / "historical_revisions_raw.csv"
OUTPUT = BASE / "cleaned"
OUTPUT.mkdir(exist_ok=True)

df = pd.read_csv(INPUT)
original_count = len(df)

required = [
    "article_title",
    "revision_id",
    "timestamp",
    "article_size_bytes"
]

for col in required:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# Record missing values before cleaning
quality = df.isna().sum().rename("missing_count")
quality.to_csv(OUTPUT / "missing_values.csv")

# Standardize data types
df["timestamp"] = pd.to_datetime(
    df["timestamp"], utc=True, errors="coerce"
)

for col in ["revision_id", "article_size_bytes"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove invalid records
df = df.dropna(subset=required)
df = df[df["article_size_bytes"] >= 0]

# Remove duplicate revision IDs
df = df.drop_duplicates(subset=["revision_id"])

# Preserve missing metadata
for col in ["username", "edit_comment"]:
    if col not in df:
        df[col] = pd.NA

df["edit_comment"] = df["edit_comment"].fillna("")
df["username"] = df["username"].fillna("Unknown")

# Sort within each article
df = df.sort_values(
    ["article_title", "timestamp"]
).reset_index(drop=True)

# Add analysis fields
df["year"] = df["timestamp"].dt.year
df["month"] = df["timestamp"].dt.strftime("%Y-%m")

# Difference between sampled revisions
df["sampled_size_change"] = (
    df.groupby("article_title")["article_size_bytes"].diff()
)

# Save cleaned dataset
df.to_csv(
    OUTPUT / "historical_revisions_cleaned.csv",
    index=False
)

# Save summary
summary = df.groupby("article_title").agg(
    revisions=("revision_id", "count"),
    earliest=("timestamp", "min"),
    latest=("timestamp", "max"),
    unique_editors=("username", "nunique"),
    average_size=("article_size_bytes", "mean")
).reset_index()

summary.to_csv(
    OUTPUT / "article_summary.csv",
    index=False
)

print("Original records:", original_count)
print("Cleaned records:", len(df))
print("\nArticle summary:")
print(summary.to_string(index=False))
