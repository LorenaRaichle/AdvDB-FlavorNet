from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from pathlib import Path
import json, random, os, warnings

# --- config ---
JSONL = Path("/mongoDB/init/03_recipe_csv_sample.jsonl")
SAMPLE_SIZE = 100_000
ARTIFACT_DIR = Path("/vectorDB/BERTartifact")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Optional: suppress the known hdbscan warnings you saw
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="invalid escape sequence.*", category=SyntaxWarning)

# Reproducibility
random.seed(42)

def iter_docs(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                yield json.loads(s)

def text_of(doc: dict) -> str:
    title = (doc.get("title") or "").strip()
    steps = " ".join(doc.get("steps") or [])
    return f"{title}. {steps}".strip()

# 1) sample
# 1) sample
docs = [(d.get("slug") or "", text_of(d)) for d in iter_docs(JSONL)]
# keep only docs that actually have a slug/text
docs = [(s, t) for (s, t) in docs if s and t]
random.shuffle(docs)

if len(docs) > SAMPLE_SIZE:
    docs = docs[:SAMPLE_SIZE]

slugs, texts = zip(*docs) if docs else ([], [])



if not texts:
    raise SystemExit("No texts found — check JSONL path or data.")

# 2) model & vectorizer
st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
vectorizer_model = CountVectorizer(
    ngram_range=(1, 2),
    stop_words="english",
    min_df=10
)

topic_model = BERTopic(
    embedding_model=st_model,
    vectorizer_model=vectorizer_model,
    low_memory=True,      # better for big corpora
    min_topic_size=300,   # broader, cleaner topics; reduce later for more granularity
    verbose=True
)

topics, probs = topic_model.fit_transform(list(texts))

# 3) inspect + save
topic_info = topic_model.get_topic_info()
print(topic_info.head(10))

topic_model.save(ARTIFACT_DIR / "bertopic_model")
topic_info.to_csv(ARTIFACT_DIR / "topic_info.csv", index=False)

# Also save top terms per topic for UI/faceting later
terms_json = {}
for topic_id in topic_info["Topic"]:
    if topic_id == -1:
        continue  # outliers
    terms = topic_model.get_topic(topic_id) or []
    terms_json[int(topic_id)] = [w for (w, _w) in terms[:8]]
with (ARTIFACT_DIR / "topic_terms.json").open("w", encoding="utf-8") as f:
    json.dump(terms_json, f, ensure_ascii=False, indent=2)

print(f"Saved to {ARTIFACT_DIR}/ (model, topic_info.csv, topic_terms.json)")