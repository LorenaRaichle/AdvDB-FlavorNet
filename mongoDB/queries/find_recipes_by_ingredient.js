// queries/find_recipes_by_ingredient.js
const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';
const ING = (typeof ING !== 'undefined') ? ING.toLowerCase() : 'garlic';
const dbx = db.getSiblingDB(DB_NAME);
printjson(
  dbx.recipes.find({ "ingredients.name": ING }, { title: 1, cuisine: 1, tags: 1 })
    .limit(10).toArray()
);
