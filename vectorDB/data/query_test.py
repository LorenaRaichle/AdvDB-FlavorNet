#!/usr/bin/env python3
"""
Quick Qdrant sanity-check:
- Connects with a generous timeout (and prefers gRPC if available)
- Prints collection status & basic config
- Gets an approximate count (fast, exact=False)
- Scrolls a few points to verify queries work without embeddings
"""

import os
import sys
import time
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException


DEFAULT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_API_KEY = os.getenv("QDRANT_API_KEY")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "recipes")

TIMEOUT_SECONDS = float(os.getenv("QDRANT_TIMEOUT", "120.0"))
SCROLL_LIMIT = int(os.getenv("QDRANT_SCROLL_LIMIT", "5"))


def make_client(url: str, api_key: Optional[str], timeout: float) -> QdrantClient:
    """
    Try to enable gRPC if the installed client supports it. Fall back to HTTP.
    """
    # Try prefer_grpc (newer clients)
    try:
        return QdrantClient(url=url, api_key=api_key, timeout=timeout, prefer_grpc=True)
    except TypeError:
        # Try grpc=True (older flag)
        try:
            return QdrantClient(url=url, api_key=api_key, timeout=timeout, grpc=True)
        except TypeError:
            # Fall back to plain HTTP
            return QdrantClient(url=url, api_key=api_key, timeout=timeout)


def robust_count(client: QdrantClient, collection: str, exact: bool = False,
                 retries: int = 3, backoff: float = 2.0) -> int:
    """
    Count with basic retries to dodge transient timeouts.
    """
    last_err = None
    for i in range(retries):
        try:
            return client.count(collection, count_filter=None, exact=exact).count
        except Exception as e:
            last_err = e
            if i < retries - 1:
                sleep_s = backoff ** i
                print(f"[warn] count(exact={exact}) failed: {e!r}. Retrying in {sleep_s:.1f}s...")
                time.sleep(sleep_s)
    # bubble up the last error if we gave up
    raise last_err


def print_collection_info(client: QdrantClient, collection: str) -> None:
    info = client.get_collection(collection)
    print(f"Collection: {collection}")
    try:
        status = getattr(info, "status", None)
        print(f"  status: {status}")
    except Exception:
        pass

    # points_count is sometimes nested under 'points_count' or 'vectors_count'; handle gracefully
    try:
        # Newer clients expose 'points_count' and 'indexed_vectors_count'
        pc = getattr(info, "points_count", None)
        if pc is not None:
            print(f"  points_count (server): {pc}")
    except Exception:
        pass

    try:
        cfg = getattr(info, "config", None)
        if cfg:
            print(f"  config: {cfg}")
    except Exception:
        pass


def sanity_scroll(client: QdrantClient, collection: str, limit: int = 5):
    """
    Scroll a few points to ensure basic queries work. We don't fetch payloads/vectors to keep it cheap.
    """
    points, next_page = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=False,
        with_vectors=False,
    )
    print(f"\nScroll sample (first {limit} point IDs):")
    if not points:
        print("  (no points returned)")
    else:
        for p in points:
            # p.id may be UUID or int
            pid = getattr(p, "id", None)
            print(f"  - {pid}")
    if next_page is not None:
        print(f"  next_page: {next_page}")


def main():
    url = DEFAULT_URL
    api_key = DEFAULT_API_KEY
    collection = DEFAULT_COLLECTION

    print(f"Connecting to Qdrant at {url} (timeout={TIMEOUT_SECONDS}s, prefer gRPC if available)...")
    client = make_client(url, api_key, TIMEOUT_SECONDS)

    # Verify collection exists
    try:
        existing = [c.name for c in client.get_collections().collections]
    except Exception as e:
        print(f"[error] Could not list collections: {e}")
        sys.exit(1)

    if collection not in existing:
        print(f"[error] Collection '{collection}' not found. Existing collections: {existing}")
        sys.exit(1)

    # Print high-level info
    try:
        print_collection_info(client, collection)
    except Exception as e:
        print(f"[warn] Could not fetch collection info cleanly: {e}")

    # Fast approximate count
    try:
        approx = robust_count(client, collection, exact=False, retries=3)
        print(f"\nApproximate total points (exact=False): {approx}")
    except (UnexpectedResponse, ResponseHandlingException, Exception) as e:
        print(f"[error] Approximate count failed: {e}")

    # Optional: exact count (can be slow). Commented out by default.
    # try:
    #     exact = robust_count(client, collection, exact=True, retries=3)
    #     print(f"Exact total points (exact=True): {exact}")
    # except Exception as e:
    #     print(f"[warn] Exact count failed (this can be normal on large collections without indexes): {e}")

    # Do a minimal query (scroll) to confirm retrieval works
    try:
        sanity_scroll(client, collection, limit=SCROLL_LIMIT)
    except Exception as e:
        print(f"[error] Scroll failed: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
