
"""
Embed recipes and upsert to Qdrant (resumable ingest).

Reads:  init/03_recipe_csv_sample.jsonl
Writes: Qdrant collection with two named vectors:
        - v_text         : embedding of title + steps
        - v_ingredients  : embedding of ingredient_tags (bag)

Environment variables (all optional):
  QDRANT_HOST=localhost
  QDRANT_PORT=6333
  QDRANT_GRPC_PORT=6334
  QDRANT_API_KEY=
  QDRANT_COLLECTION=recipes
  EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
  JSONL_PATH=mongoDB/init/03_recipe_csv_sample.jsonl
  BATCH_SIZE=128
  CKPT_FILE=.qdrant_ingest.ckpt
  QDRANT_RESET=1        # only when you want to DROP & recreate
  PAYLOAD_FIELDS=title,slug,ingredient_tags,dietary_tags,cuisine,course
"""

import os, json, sys, hashlib, time
from pathlib import Path
from typing import Dict, Any, Iterable, List
from dotenv import load_dotenv
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    OptimizersConfigDiff,
    PointStruct,
)

load_dotenv()
# ---------------------- Config ----------------------
HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
PORT = int(os.getenv("QDRANT_PORT", "6333"))
GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION = os.getenv("QDRANT_COLLECTION", "recipes")

MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
JSONL_PATH = Path(os.getenv("JSONL_PATH", "/Users/Lorena/Developer/FlavorNet/mongoDB/init/03_recipe_csv_sample.jsonl"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "128"))
CKPT_FILE = Path(os.getenv("CKPT_FILE", ".qdrant_ingest.ckpt"))
RESET = os.getenv("QDRANT_RESET", "0") == "1"


BERTOPIC_MODEL_PATH = os.getenv("BERTOPIC_MODEL_PATH")
ADD_TOPIC = os.getenv("ADD_TOPIC", "0") == "1"
TOPIC_TERMS_PATH = os.getenv("TOPIC_TERMS_PATH")
SAMPLE_PAYLOADS = int(os.getenv("SAMPLE_PAYLOADS", "10"))



PAYLOAD_FIELDS = set(
    k.strip() for k in os.getenv("PAYLOAD_FIELDS", "").split(",") if k.strip()
)

TEXT_VECTOR_NAME = "v_text"
ING_VECTOR_NAME = "v_ingredients"


# LOAD BERTmodel
topic_model = None
topic_terms = {}

print(f"[cfg] ADD_TOPIC={ADD_TOPIC}  BERTOPIC_MODEL_PATH={BERTOPIC_MODEL_PATH!r}", file=sys.stderr)
if ADD_TOPIC and (not BERTOPIC_MODEL_PATH or not Path(BERTOPIC_MODEL_PATH).exists()):
    print("[cfg] ERROR: ADD_TOPIC=1 but BERTOPIC_MODEL_PATH missing/invalid", file=sys.stderr)
    sys.exit(3)

if ADD_TOPIC:
    from bertopic import BERTopic
    print(f"Loading BERTopic from: {BERTOPIC_MODEL_PATH}")
    if not BERTOPIC_MODEL_PATH:
        print("ERROR: ADD_TOPIC=1 but BERTOPIC_MODEL_PATH is not set", file=sys.stderr)
        sys.exit(3)
    topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
    if TOPIC_TERMS_PATH and Path(TOPIC_TERMS_PATH).exists():
        import json
        with open(TOPIC_TERMS_PATH, "r", encoding="utf-8") as f:
            topic_terms = json.load(f)


# ---------------------- Helpers ----------------------
class QdrantUnavailable(RuntimeError):
    def __init__(self, message: str, last_error: Exception | None = None) -> None:
        super().__init__(message)
        self.last_error = last_error


def stable_id(slug: str) -> int:
    h = hashlib.sha256((slug or "").encode("utf-8")).hexdigest()
    return int(h[:15], 16)


def make_client(use_grpc: bool = True) -> QdrantClient:
    return QdrantClient(
        host=HOST,
        port=PORT,
        grpc_port=GRPC_PORT if use_grpc else None,
        prefer_grpc=use_grpc,
        api_key=API_KEY,
        timeout=120.0,
        check_compatibility=False,
    )


def build_text_input(doc: Dict[str, Any]) -> str:
    title = (doc.get("title") or "").strip()
    steps = " ".join(doc.get("steps") or [])
    return f"{title}. {steps}".strip()


def build_ing_input(doc: Dict[str, Any]) -> str:
    tags = doc.get("ingredient_tags") or []
    return " ".join(tags)


def build_payload(doc: Dict[str, Any]) -> Dict[str, Any]:
    full = {
        "title": doc.get("title"),
        "slug": doc.get("slug"),
        "dietary_tags": doc.get("dietary_tags") or [],
        "allergen_tags": doc.get("allergen_tags") or [],
        "flavour_tags": doc.get("flavour_tags") or [],
        "technique_tags": doc.get("technique_tags") or [],
        "ingredient_tags": doc.get("ingredient_tags") or [],
    }
    if not PAYLOAD_FIELDS:
        return full
    return {k: full.get(k) for k in PAYLOAD_FIELDS if k in full}


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            yield json.loads(s)


def read_ckpt() -> int:
    try:
        return int(CKPT_FILE.read_text().strip())
    except Exception:
        return 0


def write_ckpt_lines(n_lines: int) -> None:
    CKPT_FILE.write_text(str(n_lines))


def _is_conn_error(exc: Exception) -> bool:
    msg = (str(exc) or "").lower()
    return any(
        token in msg
        for token in (
            "unavailable",
            "failed to connect",
            "connection refused",
            "connecterror",
            "timed out",
            "timeout",
            "deadline exceeded",
        )
    )


def wait_for_service(client: QdrantClient, attempts: int = 5, delay: float = 2.0) -> None:
    last_err: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            client.get_collections()
            return
        except Exception as exc:
            if not _is_conn_error(exc):
                raise
            last_err = exc
            if attempt < attempts:
                print(
                    f"Attempt {attempt}/{attempts}: Qdrant unavailable ({exc}). Retrying in {delay:.1f}s…",
                    file=sys.stderr,
                )
                time.sleep(delay)
    raise QdrantUnavailable("Qdrant service is not reachable", last_err)


def ensure_client_connection() -> QdrantClient:
    client = make_client(use_grpc=True)
    try:
        wait_for_service(client)
        return client
    except QdrantUnavailable as grpc_err:
        print("gRPC unavailable, retrying connection over HTTP…")
        http_client = make_client(use_grpc=False)
        wait_for_service(http_client)
        return http_client


# ---------------------- Upsert utils ----------------------
def _chunk(points, n):
    for i in range(0, len(points), n):
        yield points[i : i + n]


def _safe_upsert(client: QdrantClient, collection_name: str, chunk: List[PointStruct]) -> QdrantClient:
    try:
        client.upsert(collection_name=collection_name, points=chunk, wait=True)
        return client
    except AssertionError:
        client.upsert(collection_name=collection_name, points=chunk)
        return client
    except Exception as e:
        if _is_conn_error(e):
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
                    time.sleep(base_sleep * (2**attempt))
                    if attempt == max_retries - 1:
                        raise last_err
    return client


#include Bertopics here
def upsert_batch(
    client: QdrantClient,
    model: SentenceTransformer,
    docs: List[Dict[str, Any]],
    texts: List[str],
    ings: List[str],
    topic_model=None,
    topic_terms: dict | None = None,
    sample_quota: int = 0,
) -> tuple[QdrantClient, int, List[Dict[str, Any]]]:
    text_vecs = model.encode(texts, normalize_embeddings=True)
    ing_vecs  = model.encode(ings,  normalize_embeddings=True)

    # --- topic inference (optional) ---
    topics = None
    probs = None
    if topic_model is not None:
        topics, probs = topic_model.transform(texts, embeddings=text_vecs)
        # standardize to Python lists for easy indexing/printing
        if topics is not None and hasattr(topics, "tolist"):
            topics = topics.tolist()
        if probs is not None and hasattr(probs, "tolist"):
            probs = probs.tolist()

        # optional quick log
        assigned = sum(1 for t in topics if (t is not None and t != -1))
        outliers = len(topics) - assigned
        print(f"[topics] assigned={assigned} outliers={outliers}")

    points: List[PointStruct] = []
    samples: List[Dict[str, Any]] = []

    for i, (doc, v_text, v_ing) in enumerate(zip(docs, text_vecs, ing_vecs)):
        slug = (doc.get("slug") or "").strip()
        if not slug:
            continue

        payload = build_payload(doc)

        # attach topic metadata (if available)
        if topics is not None:
            t_id = topics[i]
            t_prob = probs[i] if probs is not None else None
            if t_id is not None and t_id != -1:
                payload["topic_id"] = int(t_id)
                if t_prob is not None:
                    payload["topic_score"] = float(t_prob)
                if topic_terms:
                    payload["topic_terms"] = topic_terms.get(str(t_id)) or topic_terms.get(int(t_id)) or []
            else:
                payload["topic_id"] = None
                payload["topic_score"] = None

        points.append(PointStruct(
            id=stable_id(slug),
            vector={"v_text": v_text.tolist(), "v_ingredients": v_ing.tolist()},
            payload=payload,
        ))

        if len(samples) < sample_quota:
            samples.append(payload)

    if points:
        client = upsert_with_retry(client, COLLECTION, points)
    return client, len(points), samples




def count_lines(path: Path) -> int:
    """Return total number of lines in the JSONL file (including blanks)."""
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


# ---------------------- Collection management ----------------------
def ensure_collection(client: QdrantClient, dim: int) -> QdrantClient:
    exists = hasattr(client, "collection_exists") and client.collection_exists(COLLECTION)
    if exists and not RESET:
        return client
    if exists and RESET:
        print(f"RESET=1 → deleting existing collection '{COLLECTION}'…")
        client.delete_collection(COLLECTION)

    def _create_with(client_obj: QdrantClient) -> QdrantClient:
        client_obj.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                TEXT_VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE),
                ING_VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE),
            },
            optimizers_config=OptimizersConfigDiff(default_segment_number=2),
        )
        return client_obj

    print(f"Creating new collection '{COLLECTION}' (dim={dim})…")
    return _create_with(client)


# ---------------------- Main ----------------------
def main() -> None:
    if not JSONL_PATH.exists():
        print(f"ERROR: JSONL not found at {JSONL_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Connecting to Qdrant: {HOST}:{PORT} (gRPC {GRPC_PORT}), collection={COLLECTION}")
    client = ensure_client_connection()

    dim = int(model.encode(["probe"], normalize_embeddings=True)[0].shape[0])
    client = ensure_collection(client, dim)

    total_lines = count_lines(JSONL_PATH)
    lines_done = read_ckpt()
    points_done = 0

    printed = 0  # how many payload samples we showed so far

    print(f"Embedding & upserting ~{total_lines} docs in batches of {BATCH_SIZE}…")
    with tqdm(total=total_lines, unit="line", initial=lines_done) as pbar:
        to_embed_text, to_embed_ing, docs_cache = [], [], []
        for idx, doc in enumerate(iter_jsonl(JSONL_PATH), start=1):
            if idx <= lines_done:
                continue

            to_embed_text.append(build_text_input(doc))
            to_embed_ing.append(build_ing_input(doc))
            docs_cache.append(doc)

            if len(docs_cache) >= BATCH_SIZE:
                # ask upsert_batch to give us up to the remaining sample quota
                quota = max(0, SAMPLE_PAYLOADS - printed)
                client, n, samples = upsert_batch(
                    client, model, docs_cache, to_embed_text, to_embed_ing,
                    topic_model=topic_model, topic_terms=topic_terms,
                    sample_quota=quota
                )
                # print any samples returned
                for sp in samples:
                    print("\n[PAYLOAD SAMPLE]")
                    print(json.dumps(sp, ensure_ascii=False, indent=2))
                    printed += 1
                    if printed >= SAMPLE_PAYLOADS:
                        break

                points_done += n
                lines_done = idx
                write_ckpt_lines(lines_done)
                pbar.update(len(docs_cache))
                print(f"[batch] upserted {n} unique points (line {idx}/{total_lines})")
                docs_cache, to_embed_text, to_embed_ing = [], [], []

        if docs_cache:
            quota = max(0, SAMPLE_PAYLOADS - printed)
            client, n, samples = upsert_batch(
                client, model, docs_cache, to_embed_text, to_embed_ing,
                topic_model=topic_model, topic_terms=topic_terms,
                sample_quota=quota
            )
            for sp in samples:
                print("\n[PAYLOAD SAMPLE]")
                print(json.dumps(sp, ensure_ascii=False, indent=2))
                printed += 1
                if printed >= SAMPLE_PAYLOADS:
                    break

            points_done += n
            lines_done = total_lines
            write_ckpt_lines(lines_done)
            pbar.update(len(docs_cache))
            print(f"[last batch] upserted {n} points.")


    print(f"Done. Processed {lines_done} lines, upserted ~{points_done} unique slugs into '{COLLECTION}'.")


if __name__ == "__main__":
    main()
