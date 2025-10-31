// Run: mongosh --file find_recipes_by_filters.js --eval "DB_NAME='appdb';DIET='vegan';FLAV='spicy';ING='chickpeas'"
const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';
const DIET = (typeof DIET !== 'undefined' && DIET) ? DIET : null;
const FLAV = (typeof FLAV !== 'undefined' && FLAV) ? FLAV : null;
const ING  = (typeof ING !== 'undefined'  && ING)  ? ING  : null;

const dbx = db.getSiblingDB(DB_NAME);
const q = {};
if (DIET) q.dietary_tags   = DIET.toLowerCase();
if (FLAV) q.flavour_tags   = FLAV.toLowerCase();
if (ING)  q.ingredient_tags= ING.toLowerCase();

printjson(
  dbx.recipes.find(q, { title:1, cuisine:1, course:1, dietary_tags:1, flavour_tags:1 })
    .sort({ "rating.value": -1 })
    .limit(10).toArray()
);
