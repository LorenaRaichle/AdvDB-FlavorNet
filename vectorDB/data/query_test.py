from qdrant_client import QdrantClient
c = QdrantClient(host="127.0.0.1", port=6333, check_compatibility=False)

print("Total points so far:", c.count("recipes", exact=True).count)

# Simple nearest-neighbor on v_text
from sentence_transformers import SentenceTransformer
st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
qvec = st.encode(["creamy baked pasta"], normalize_embeddings=True)[0].tolist()

hits = c.search(
    collection_name="recipes",
    query_vector=("v_text", qvec),
    limit=5
)
for h in hits:
    print(round(h.score, 4), h.payload.get("title"), h.payload.get("dietary_tags"))