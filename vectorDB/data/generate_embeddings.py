#!/usr/bin/env python3
"""
Embed recipes and upsert to Qdrant.

Reads:  init/03_recipe_csv_sample.jsonl
Writes: Qdrant collection with two named vectors:
        - v_text         : embedding of title + steps
        - v_ingredients  : embedding of ingredient_tags (bag)

Env vars (all optional):
  QDRANT_HOST=localhost
  QDRANT_PORT=6333
  QDRANT_API_KEY=          # if using Qdrant Cloud
  QDRANT_COLLECTION=recipes
  EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
  JSONL_PATH=mongoDB/init/03_recipe_csv_sample.jsonl
  BATCH_SIZE=256
"""

import os, json, sys, hashlib
from pathlib import Path
from typing import Dict, Any, Iterable, List

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, OptimizersConfigDiff, PointStruct



from sentence_transformers import SentenceTransformer


# ---------------------- Config ----------------------
HOST = os.getenv("QDRANT_HOST", "localhost")
PORT = int(os.getenv("QDRANT_PORT", "6333"))
API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION = os.getenv("QDRANT_COLLECTION", "recipes")

MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
JSONL_PATH = Path(os.getenv("JSONL_PATH", "/Users/Lorena/Developer/FlavorNet/mongoDB/init/03_recipe_csv_sample.jsonl"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "256"))

TEXT_VECTOR_NAME = "v_text"
ING_VECTOR_NAME  = "v_ingredients"

from qdrant_client import QdrantClient
from tqdm import tqdm
client = QdrantClient(
    host=HOST,
    port=PORT,
    api_key=API_KEY,
    check_compatibility=False,  # add this
)
# ---------------------- Helpers ----------------------
def stable_id(slug: str) -> int:
    """Deterministic positive 64-bit-ish int from slug."""
    h = hashlib.sha256(slug.encode("utf-8")).hexdigest()
    return int(h[:15], 16)  # fits in signed 64-bit for Qdrant

def build_text_input(doc: Dict[str, Any]) -> str:
    title = (doc.get("title") or "").strip()
    steps = " ".join(doc.get("steps") or [])
    return f"{title}. {steps}".strip()

def build_ing_input(doc: Dict[str, Any]) -> str:
    tags = doc.get("ingredient_tags") or []
    # join with spaces -> bag of ingredients
    return " ".join(tags)

def build_payload(doc: Dict[str, Any]) -> Dict[str, Any]:
    rating = (doc.get("rating") or {}).get("value")
    return {
        "title": doc.get("title"),
        "slug": doc.get("slug"),
        "dietary_tags": doc.get("dietary_tags") or [],
        "allergen_tags": doc.get("allergen_tags") or [],
        "flavour_tags": doc.get("flavour_tags") or [],
        "technique_tags": doc.get("technique_tags") or [],
        "ingredient_tags": doc.get("ingredient_tags") or [],
        "cuisine": doc.get("cuisine"),
        "course": doc.get("course"),
        "rating_value": rating,
        "source_url": doc.get("source_url"),
    }

def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)



def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def main() -> None:
    if not JSONL_PATH.exists():
        print(f"ERROR: JSONL not found at {JSONL_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Connecting to Qdrant: {HOST}:{PORT}, collection={COLLECTION}")
    client = QdrantClient(
        host=HOST,
        port=PORT,
        api_key=API_KEY,
        check_compatibility=False,   # silence version warning
    )

    _probe_vec = model.encode(["probe"], normalize_embeddings=True)[0]
    dim = int(_probe_vec.shape[0])

    print("Creating/recreating collection...")
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config={
            TEXT_VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE),
            ING_VECTOR_NAME:  VectorParams(size=dim, distance=Distance.COSINE),
        },
        optimizers_config=OptimizersConfigDiff(default_segment_number=2),
    )

    total_lines = count_lines(JSONL_PATH)
    print(f"Embedding & upserting ~{total_lines} docs in batches of {BATCH_SIZE}…")

    batch_points, to_embed_text, to_embed_ing, docs_cache = [], [], [], []
    total = 0

    with tqdm(total=total_lines, unit="doc") as pbar:
        for doc in iter_jsonl(JSONL_PATH):
            text_input = build_text_input(doc)
            ing_input  = build_ing_input(doc)

            to_embed_text.append(text_input)
            to_embed_ing.append(ing_input)
            docs_cache.append(doc)

            if len(docs_cache) >= BATCH_SIZE:
                n = upsert_batch(client, model, docs_cache, to_embed_text, to_embed_ing)
                total += n
                pbar.update(n)
                print(f"[batch] upserted: {n} (total: {total})")
                docs_cache, to_embed_text, to_embed_ing = [], [], []

        if docs_cache:
            n = upsert_batch(client, model, docs_cache, to_embed_text, to_embed_ing)
            total += n
            pbar.update(n)
            print(f"[batch] upserted: {n} (total: {total})")

    print(f"Done. Upserted {total} points into '{COLLECTION}'.")


def upsert_batch(client: QdrantClient, model: SentenceTransformer,
                 docs: List[Dict[str, Any]],
                 texts: List[str], ings: List[str]) -> int:

    # Encode (normalized for cosine)
    text_vecs = model.encode(texts, normalize_embeddings=True)
    ing_vecs  = model.encode(ings,  normalize_embeddings=True)

    points = []
    for doc, v_text, v_ing in zip(docs, text_vecs, ing_vecs):
        slug = (doc.get("slug") or "").strip()
        if not slug:
            # skip malformed docs without slug
            continue

        points.append(PointStruct(
            id=stable_id(slug),
            vector={
                TEXT_VECTOR_NAME: v_text.tolist(),
                ING_VECTOR_NAME:  v_ing.tolist(),
            },
            payload=build_payload(doc),
        ))

    if points:
        client.upsert(collection_name=COLLECTION, points=points)
    return len(points)

if __name__ == "__main__":
    main()
