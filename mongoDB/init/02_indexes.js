// 02_indexes.js
const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';
const dbx = db.getSiblingDB(DB_NAME);

dbx.recipes.createIndex(
  { title: "text", tags: "text", "ingredients.raw": "text" },
  { name: "recipes_text" }
);

dbx.recipes.createIndex({ cuisine: 1, "rating.value": -1 }, { name: "cuisine_rating" });
dbx.recipes.createIndex({ course: 1 }, { name: "course" });

dbx.recipes.createIndex({ "ingredients.name": 1 },   { name: "ingredient_name" });
dbx.recipes.createIndex({ ingredient_tags: 1 },      { name: "ingredient_tags" });
dbx.recipes.createIndex({ dietary_tags: 1 },         { name: "dietary_tags" });
dbx.recipes.createIndex({ allergen_tags: 1 },        { name: "allergen_tags" });
dbx.recipes.createIndex({ flavour_tags: 1 },         { name: "flavour_tags" });
dbx.recipes.createIndex({ technique_tags: 1 },       { name: "technique_tags" });

try { dbx.recipes.dropIndex("slug_unique"); } catch (e) {}
dbx.recipes.createIndex({ slug: 1, source_url: 1 }, { name: "slug_source_unique", unique: true, sparse: true });

dbx.comments.createIndex({ recipe_id: 1, created_at: -1 }, { name: "comments_by_recipe" });
dbx.users_public.createIndex({ username: 1 }, { unique: true });

print("Indexes created (arrays + cuisine).");
