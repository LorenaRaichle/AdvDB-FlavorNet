#!/usr/bin/env python3
from pathlib import Path
import json

JSONL = Path("/Users/Lorena/Developer/FlavorNet/mongoDB/init/03_recipe_csv_sample.jsonl")

total_lines = 0
with_slug = 0
slugs = []
blank = 0
bad = 0

with JSONL.open("r", encoding="utf-8") as f:
    for line in f:
        s = line.strip()
        if not s:
            blank += 1
            continue
        total_lines += 1
        try:
            doc = json.loads(s)
        except Exception:
            bad += 1
            continue
        slug = (doc.get("slug") or "").strip()
        if slug:
            with_slug += 1
            slugs.append(slug)

unique_slugs = len(set(slugs))
dupe_slugs = with_slug - unique_slugs

print(f"Total non-empty lines: {total_lines}")
print(f"Lines with slug:       {with_slug}")
print(f"Unique slugs:          {unique_slugs}")
print(f"Duplicate slugs:       {dupe_slugs}")
print(f"Blank lines:           {blank}")
print(f"Bad JSON lines:        {bad}")
