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
  QDRANT_GRPC_PORT=6334
  QDRANT_API_KEY=
  QDRANT_COLLECTION=recipes
  EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
  JSONL_PATH=mongoDB/init/03_recipe_csv_sample.jsonl
  BATCH_SIZE=128
  CKPT_FILE=.qdrant_ingest.ckpt
"""

import os, json, sys, hashlib, time
from pathlib import Path
from typing import Dict, Any, Iterable, List

from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    OptimizersConfigDiff,
    PointStruct,
)

# ---------------------- Config ----------------------
HOST = os.getenv("QDRANT_HOST", "127.0.0.1")        # force IPv4 to avoid ::1 issues
PORT = int(os.getenv("QDRANT_PORT", "6333"))
GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION = os.getenv("QDRANT_COLLECTION", "recipes")

MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
JSONL_PATH = Path(os.getenv("JSONL_PATH", "/Users/Lorena/Developer/FlavorNet/mongoDB/init/03_recipe_csv_sample.jsonl"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "128"))
CKPT_FILE = Path(os.getenv("CKPT_FILE", ".qdrant_ingest.ckpt"))

TEXT_VECTOR_NAME = "v_text"
ING_VECTOR_NAME  = "v_ingredients"


# ---------------------- Helpers ----------------------
def stable_id(slug: str) -> int:
    """Deterministic positive int id."""
    h = hashlib.sha256((slug or "").encode("utf-8")).hexdigest()
    return int(h[:15], 16)

def make_client(use_grpc: bool = True) -> QdrantClient:
    """Create a Qdrant client; prefer gRPC when available."""
    return QdrantClient(
        host=HOST,
        port=PORT,
        grpc_port=GRPC_PORT if use_grpc else None,
        prefer_grpc=use_grpc,
        api_key=API_KEY,
        timeout=120.0,
        check_compatibility=False,  # your client/server versions differ
    )

def build_text_input(doc: Dict[str, Any]) -> str:
    title = (doc.get("title") or "").strip()
    steps = " ".join(doc.get("steps") or [])
    return f"{title}. {steps}".strip()

def build_ing_input(doc: Dict[str, Any]) -> str:
    tags = doc.get("ingredient_tags") or []
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
            s = line.strip()
            if not s:
                continue
            yield json.loads(s)

def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def read_ckpt() -> int:
    try:
        return int(CKPT_FILE.read_text().strip())
    except Exception:
        return 0

def write_ckpt(n_done: int) -> None:
    CKPT_FILE.write_text(str(n_done))


# ---------------------- Upsert utils ----------------------
def _chunk(points, n):
    for i in range(0, len(points), n):
        yield points[i:i+n]

def _safe_upsert(client: QdrantClient, collection_name: str, chunk: List[PointStruct]) -> QdrantClient:
    """
    Version-tolerant upsert:
      * some clients accept wait=True, others reject kwargs
      * if gRPC connection fails, auto-switch to HTTP and retry once
    Returns the (possibly replaced) client to continue with.
    """
    try:
        client.upsert(collection_name=collection_name, points=chunk, wait=True)
        return client
    except AssertionError:
        # kwargs not accepted → retry without extras
        client.upsert(collection_name=collection_name, points=chunk)
        return client
    except Exception as e:
        msg = (str(e) or "").lower()
        if "unavailable" in msg or "failed to connect" in msg or "connection refused" in msg:
            http_client = make_client(use_grpc=False)
            http_client.upsert(collection_name=collection_name, points=chunk)
            return http_client
        raise

def upsert_with_retry(
    client: QdrantClient,
    collection_name: str,
    points: List[PointStruct],
    max_retries: int = 5,
    base_sleep: float = 1.0,
) -> QdrantClient:
    """
    Upsert with backoff and sub-chunk fallback. Returns the (possibly replaced) client.
    """
    try_sizes = [len(points), 128, 64, 32, 16]
    last_err = None
    for size in try_sizes:
        for chunk in _chunk(points, size):
            for attempt in range(max_retries):
                try:
                    client = _safe_upsert(client, collection_name, chunk)
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(base_sleep * (2 ** attempt))
                    if attempt == max_retries - 1:
                        raise last_err
    return client

def upsert_batch(
    client: QdrantClient,
    model: SentenceTransformer,
    docs: List[Dict[str, Any]],
    texts: List[str],
    ings: List[str],
) -> tuple[QdrantClient, int]:
    """Embed a batch, build points, upsert with retry. Returns (client, n_points)."""
    text_vecs = model.encode(texts, normalize_embeddings=True)
    ing_vecs  = model.encode(ings,  normalize_embeddings=True)

    points: List[PointStruct] = []
    for doc, v_text, v_ing in zip(docs, text_vecs, ing_vecs):
        slug = (doc.get("slug") or "").strip()
        if not slug:
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
        client = upsert_with_retry(client, COLLECTION, points)
    return client, len(points)


# ---------------------- Collection management ----------------------
def ensure_collection(client: QdrantClient, dim: int) -> None:
    """
    Try non-deprecated exists+create; if unsupported by server/client, fall back to recreate_collection.
    Works across older client/server versions.
    """
    try:
        # Newer clients:
        if hasattr(client, "collection_exists") and client.collection_exists(COLLECTION):
            client.delete_collection(COLLECTION)
        if hasattr(client, "create_collection"):
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config={
                    TEXT_VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE),
                    ING_VECTOR_NAME:  VectorParams(size=dim, distance=Distance.COSINE),
                },
                optimizers_config=OptimizersConfigDiff(default_segment_number=2),
            )
            return
        # If create_collection isn't available, drop to except to use recreate
        raise AttributeError("create_collection not available on this client")
    except Exception:
        # Older clients/servers:
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config={
                TEXT_VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE),
                ING_VECTOR_NAME:  VectorParams(size=dim, distance=Distance.COSINE),
            },
            optimizers_config=OptimizersConfigDiff(default_segment_number=2),
        )


# ---------------------- Main ----------------------
def main() -> None:
    if not JSONL_PATH.exists():
        print(f"ERROR: JSONL not found at {JSONL_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Connecting to Qdrant: {HOST}:{PORT} (gRPC {GRPC_PORT}), collection={COLLECTION}")
    client = make_client(use_grpc=True)

    # infer vector size once
    dim = int(model.encode(["probe"], normalize_embeddings=True)[0].shape[0])

    print("Creating collection (or recreating if exists)…")
    ensure_collection(client, dim)

    total_lines = count_lines(JSONL_PATH)
    print(f"Embedding & upserting ~{total_lines} docs in batches of {BATCH_SIZE}…")

    to_embed_text: List[str] = []
    to_embed_ing:  List[str] = []
    docs_cache:    List[Dict[str, Any]] = []
    total = read_ckpt()

    with tqdm(total=total_lines, unit="doc", initial=total) as pbar:
        for idx, doc in enumerate(iter_jsonl(JSONL_PATH), start=1):
            # resume support: skip already-processed lines
            if idx <= total:
                continue

            to_embed_text.append(build_text_input(doc))
            to_embed_ing.append(build_ing_input(doc))
            docs_cache.append(doc)

            if len(docs_cache) >= BATCH_SIZE:
                client, n = upsert_batch(client, model, docs_cache, to_embed_text, to_embed_ing)
                total += n
                write_ckpt(total)
                pbar.update(n)
                print(f"[batch] upserted: {n} (total: {total})")
                docs_cache, to_embed_text, to_embed_ing = [], [], []

        # last partial batch
        if docs_cache:
            client, n = upsert_batch(client, model, docs_cache, to_embed_text, to_embed_ing)
            total += n
            write_ckpt(total)
            pbar.update(n)
            print(f"[batch] upserted: {n} (total: {total})")

    print(f"Done. Upserted {total} points into '{COLLECTION}'.")


if __name__ == "__main__":
    main()
