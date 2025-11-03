#!/usr/bin/env python3
"""
query_test.py — sanity checks for the 'recipes' Qdrant collection.

What it does:
  1) Prints collection status and a hint of the vector schema
  2) Prints exact & fast (approx) counts
  3) Prints a couple of filtered counts (dietary/allergen tags)
  4) Runs quick top-5 searches on both named vectors: v_text and v_ingredients
"""

import inspect
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from sentence_transformers import SentenceTransformer

# ---- Config ----
HOST = "127.0.0.1"
PORT = 6333
COLLECTION = "recipes"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---- Helpers ----
def count_points(client: QdrantClient, collection: str, flt: Filter | None = None, exact: bool = True) -> int:
    """
    Version-tolerant wrapper around QdrantClient.count().
    Different client versions use different kwarg names:
      - filter
      - query_filter
      - count_filter
    Falls back to positional if needed.
    """
    sig = inspect.signature(client.count)
    params = {p.name for p in sig.parameters.values()}

    if flt is None:
        # Unfiltered is straightforward on every version
        return client.count(collection, exact=exact).count

    if "filter" in params:
        return client.count(collection, filter=flt, exact=exact).count
    if "query_filter" in params:
        return client.count(collection, query_filter=flt, exact=exact).count
    if "count_filter" in params:
        return client.count(collection, count_filter=flt, exact=exact).count

    # Last resort: try positional (collection, filter, exact)
    try:
        return client.count(collection, flt, exact).count
    except TypeError as e:
        raise RuntimeError(
            "Unsupported qdrant-client count() signature for filtered counts"
        ) from e


def print_collection_overview(c: QdrantClient, collection: str) -> None:
    info = c.get_collection(collection)
    status = getattr(info, "status", "unknown")
    points_count = getattr(info, "points_count", "n/a")
    print(f"Collection: {collection}")
    print(f"  status: {status}")
    print(f"  points_count (server): {points_count}")

    # Try to display vector names/config in a version-safe way
    printed_schema = False
    for attr in ("vectors_config", "config", "params"):
        cfg = getattr(info, attr, None)
        if cfg:
            print(f"  {attr}: {cfg}")
            printed_schema = True
            break
    if not printed_schema:
        print("  (vector schema not available via this client's get_collection response)")


def main():
    # Connect
    c = QdrantClient(host=HOST, port=PORT, check_compatibility=False)

    # 1) Basic collection info
    print_collection_overview(c, COLLECTION)

    # 2) Counts
    total_exact = count_points(c, COLLECTION, flt=None, exact=True)
    print(f"Exact total points: {total_exact}")

    total_fast = count_points(c, COLLECTION, flt=None, exact=False)
    print(f"Fast approx total: {total_fast}")

    # 3) Filtered counts to sanity-check payload fields
    diet_filter = Filter(
        must=[
            FieldCondition(
                key="dietary_tags",
                match=MatchAny(any=["vegan", "vegetarian"]),
            )
        ]
    )
    diet_count = count_points(c, COLLECTION, flt=diet_filter, exact=True)
    print(f"With dietary tag vegan|vegetarian: {diet_count}")

    allergen_filter = Filter(
        must=[
            FieldCondition(
                key="allergen_tags",
                match=MatchAny(any=["nuts", "gluten"]),
            )
        ]
    )
    allergen_count = count_points(c, COLLECTION, flt=allergen_filter, exact=True)
    print(f"With allergen tag nuts|gluten: {allergen_count}")

    # 4) Quick KNN searches on both named vectors
    st = SentenceTransformer(MODEL)

    # v_text search
    q_text = "creamy baked pasta"
    qvec_text = st.encode([q_text], normalize_embeddings=True)[0].tolist()
    hits_text = c.search(
        collection_name=COLLECTION,
        query_vector=("v_text", qvec_text),
        limit=5,
        with_payload=True,
    )
    print(f"\nTop-5 for v_text: “{q_text}”")
    for h in hits_text:
        title = h.payload.get("title")
        diet = h.payload.get("dietary_tags")
        print(f"  {h.score:.4f}  {title}  {diet}")

    # v_ingredients search
    q_ing = "pasta cream parmesan tomato"
    qvec_ing = st.encode([q_ing], normalize_embeddings=True)[0].tolist()
    hits_ing = c.search(
        collection_name=COLLECTION,
        query_vector=("v_ingredients", qvec_ing),
        limit=5,
        with_payload=True,
    )
    print(f"\nTop-5 for v_ingredients: “{q_ing}”")
    for h in hits_ing:
        title = h.payload.get("title")
        ings = h.payload.get("ingredient_tags")
        print(f"  {h.score:.4f}  {title}  {ings}")


if __name__ == "__main__":
    main()
