import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://en.wikipedia.org/w/api.php"

# og articles
#ARTICLES = [
#    "Vietnam War",
#    "Watergate scandal",
#    "Chernobyl disaster",
#    "World War II",
#    "September 11 attacks",
#]

# new list
# Load cleaned article list
article_list_path = Path(__file__).resolve().parent.parent / "articleLists" / "cleaned_articles.txt"

with open(article_list_path, "r", encoding="utf-8") as file:
    exec(file.read())

print(f"Loaded {len(ARTICLES)} articles")

# MAX_PER_ARTICLE = 2000

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw"
RAW.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "WikipediaArchaeologyClassProject/1.0 "
        "(student research; contact: cwolver1@vols.utk.edu)"
    )
})

def collect_article(title):
    revisions = []
    continuation = {}

    # while len(revisions) < MAX_PER_ARTICLE:
    while True:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "prop": "revisions",
            "titles": title,
            "rvprop": "ids|timestamp|user|userid|comment|size|flags",
            # "rvlimit": min(500, MAX_PER_ARTICLE - len(revisions)),
            "rvlimit": 500,
            "rvdir": "older",
            "maxlag": 5,
            **continuation
        }

        for attempt in range(5):
            try:
                response = session.get(
                    API, params=params, timeout=30
                )

                if response.status_code in (429, 503):
                    wait = min(60, 2 ** attempt * 5)
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                result = response.json()

                if result.get("error", {}).get("code") == "maxlag":
                    time.sleep(5 * (attempt + 1))
                    continue

                if "error" in result:
                    raise RuntimeError(result["error"])

                break
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError("API retries exhausted")

        pages = result.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            raise ValueError(f"Article not found: {title}")

        revisions.extend(pages[0].get("revisions", []))
        continuation = result.get("continue", {})

        print(f"{title}: {len(revisions)} revisions")

        if not continuation:
            break

        time.sleep(1)

    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")

    with open(RAW / f"{slug}.json", "w") as f:
        json.dump({
            "article": title,
            "revisions": revisions
        }, f, indent=2)

    rows = []
    for r in revisions:
        rows.append({
            "article_title": title,
            "revision_id": r.get("revid"),
            "parent_id": r.get("parentid"),
            "timestamp": r.get("timestamp"),
            "username": r.get("user"),
            "user_id": r.get("userid"),
            "edit_comment": r.get("comment"),
            "article_size_bytes": r.get("size"),
            "is_minor": "minor" in r,
            "user_hidden": "userhidden" in r,
            "comment_hidden": "commenthidden" in r
        })

    return rows

all_rows = []

for article in ARTICLES:
    try:
        all_rows.extend(collect_article(article))
    except Exception as e:
        print(f"FAILED: {article}: {e}")

df = pd.DataFrame(all_rows)
output = BASE / "historical_revisions_raw.csv"
df.to_csv(output, index=False)

print(f"\nSaved {len(df)} records to {output}")
