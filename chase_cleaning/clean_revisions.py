import argparse
from pathlib import Path
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument(
    "--article", default="Python (programming language)"
)
args = parser.parse_args()

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
REPORTS = BASE / "reports"
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

# 1. Load the original dataset
df = pd.read_csv(args.input)
print("Original records:", len(df))

required = [
    "revision_id", "timestamp",
    "article_size_bytes"
]
missing_cols = [c for c in required if c not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns: {missing_cols}")

# 2. Record data quality issues before cleaning
issues = []

def record_issue(name, count):
    issues.append({"issue": name, "count": int(count)})

record_issue("Original records", len(df))
record_issue(
    "Duplicate revision IDs",
    df["revision_id"].duplicated().sum()
)
record_issue(
    "Missing edit comments",
    df["edit_comment"].isna().sum()
    if "edit_comment" in df else len(df)
)
record_issue(
    "Missing usernames",
    df["username"].isna().sum()
    if "username" in df else len(df)
)

# 3. Convert data types
df["timestamp"] = pd.to_datetime(
    df["timestamp"], utc=True, errors="coerce"
)
df["revision_id"] = pd.to_numeric(
    df["revision_id"], errors="coerce"
)
df["article_size_bytes"] = pd.to_numeric(
    df["article_size_bytes"], errors="coerce"
)

record_issue(
    "Invalid timestamps",
    df["timestamp"].isna().sum()
)
record_issue(
    "Invalid revision IDs",
    df["revision_id"].isna().sum()
)
record_issue(
    "Invalid article sizes",
    (
        df["article_size_bytes"].isna()
        | (df["article_size_bytes"] < 0)
    ).sum()
)

# 4. Remove invalid and duplicate records
df = df.dropna(subset=[
    "revision_id", "timestamp", "article_size_bytes"
])
df = df[df["article_size_bytes"] >= 0]
df = df.drop_duplicates(
    subset=["revision_id"], keep="first"
).copy()

df["revision_id"] = df["revision_id"].astype("int64")

# 5. Handle missing information
if "username" not in df:
    df["username"] = pd.NA

if "edit_comment" not in df:
    df["edit_comment"] = pd.NA

df["username"] = (
    df["username"].astype("string").str.strip()
)
df["edit_comment"] = (
    df["edit_comment"].fillna("").astype("string")
)

# Keep missing usernames identifiable
df["username"] = df["username"].fillna("Unknown")

# Preserve available editor metadata
if "is_anonymous" not in df:
    df["is_anonymous"] = pd.NA

df["is_anonymous"] = (
    df["is_anonymous"].astype("boolean")
)

# 6. Add standardized analysis columns
df["article_title"] = args.article
df["year"] = df["timestamp"].dt.year
df["month"] = df["timestamp"].dt.strftime("%Y-%m")
df["comment_length"] = df["edit_comment"].str.len()

# Sort chronologically
df = df.sort_values("timestamp").reset_index(drop=True)

# 7. Calculate differences between sampled revisions
# These are NOT necessarily single-edit changes.
df["size_change_sampled"] = (
    df["article_size_bytes"].diff()
)

# 8. Save cleaned data
output = DATA / "cleaned_revisions.csv"
df.to_csv(output, index=False)

# 9. Save validation report
record_issue("Cleaned records", len(df))
record_issue(
    "Remaining duplicate IDs",
    df["revision_id"].duplicated().sum()
)
record_issue(
    "Remaining invalid timestamps",
    df["timestamp"].isna().sum()
)

pd.DataFrame(issues).to_csv(
    REPORTS / "validation_report.csv",
    index=False
)

# 10. Save monthly summary for visualization
monthly = (
    df.groupby("month")
    .size()
    .reset_index(name="revision_count")
)
monthly.to_csv(
    REPORTS / "monthly_revision_counts.csv",
    index=False
)

print("\nCLEANING COMPLETE")
print("Cleaned records:", len(df))
print("Date range:", df["timestamp"].min(),
      "to", df["timestamp"].max())
print("Cleaned file:", output)
print("\nValidation report:")
print(pd.DataFrame(issues).to_string(index=False))
