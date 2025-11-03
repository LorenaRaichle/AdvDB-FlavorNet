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