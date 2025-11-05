# DOKU


## vector DB
- vectors: v_text and v_ingredients, both 384-dim cosine embeddings
  - v_text: title & steps
  - v_ingredients: ingredients
- points (recipes): 126 ,584 total
- With dietary tag vegan | vegetarian → 65 ,864 recipes
- With allergen tag nuts | gluten → 34 ,516 recipes

example point in Qdrant
{
  "id": 1234567890,
  "vector": {
    "v_text": [ ... 384 floats ... ],
    "v_ingredients": [ ... 384 floats ... ]
  },
  "payload": {
    "title": "Creamy Sundried Tomato Pasta",
    "slug": "creamy-sundried-tomato-pasta",
    "dietary_tags": ["gluten-free"],
    "allergen_tags": ["..."],
    "flavour_tags": ["..."],
    "technique_tags": ["..."],
    "ingredient_tags": ["pasta", "tomato-sauce", "parmesan", "cream"],
    "cuisine": "Italian",
    "course": "Main",
    "rating_value": 4.6,
    "source_url": "https://…"
  }
}

- info to number of entries: 03_recipe_csv_sample.jsonl -> 
- Total non-empty lines: 2231142
Lines with slug:       2231105
Unique slugs:          1242364
Duplicate slugs:       988741
Blank lines:           0
Bad JSON lines:        0


to do Qdrant
- docker compose pull qdrant
docker compose up -d qdrant
On first boot, the entrypoint sees an empty volume and unpacks your baked data into /qdrant/storage.
Check progress: docker logs -f qdrant (you’ll see the “Restoring from seed tarball…” message once).
Verify:
curl -s http://localhost:6333/collections/recipes | jq
curl -s -X POST http://localhost:6333/collections/recipes/points/count \
  -H 'Content-Type: application/json' -d '{"exact": false}' | jq