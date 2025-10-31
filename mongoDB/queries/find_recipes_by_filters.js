// Run: mongosh --file queries/find_recipes_by_ingredient.js --eval 'DB_NAME="appdb";ING="garlic"'
// Multi-ingredient: mongosh --file queries/find_recipes_by_ingredient.js --eval 'DB_NAME="appdb";ING="garlic,tomato"'

const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';
const ING_RAW = (typeof ING !== 'undefined' && ING) ? ING : 'garlic';
const INGS = ING_RAW.split(",").map(s => s.trim().toLowerCase()).filter(Boolean);

const dbx = db.getSiblingDB(DB_NAME);

const q = {};
if (INGS.length === 1) {
  q.ingredient_tags = INGS[0];
} else {
  q.ingredient_tags = { $all: INGS };
}

printjson(
  dbx.recipes
    .find(q, { title: 1, cuisine: 1, ingredient_tags: 1, "rating.value": 1 })
    .sort({ "rating.value": -1 })
    .limit(10)
    .toArray()
);

