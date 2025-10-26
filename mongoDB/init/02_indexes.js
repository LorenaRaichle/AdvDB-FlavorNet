// 02_indexes.js
const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';
const dbx = db.getSiblingDB(DB_NAME);

dbx.recipes.createIndex(
  { title: "text", tags: "text", "ingredients.raw": "text" },
  { name: "recipes_text" }
);
dbx.recipes.createIndex({ cuisine: 1, "rating.value": -1 }, { name: "cuisine_rating" });
dbx.recipes.createIndex({ "ingredients.name": 1 }, { name: "ingredient_name" });

dbx.comments.createIndex({ recipe_id: 1, created_at: -1 }, { name: "comments_by_recipe" });
dbx.users_public.createIndex({ username: 1 }, { unique: true });

print("Indexes created");
