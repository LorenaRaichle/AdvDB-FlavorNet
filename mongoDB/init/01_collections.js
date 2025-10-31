// 01_collections.js
// Run: mongosh --file 01_collections.js --eval "DB_NAME='appdb'"

const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';
const appdb = db.getSiblingDB(DB_NAME);

// ----- Controlled vocabularies (mirror these in your Python pipeline) -----
const DIETARY   = ["vegan","vegetarian","pescatarian","halal","kosher","gluten-free","dairy-free","nut-free","egg-free","low-carb","low-fat"];
const ALLERGENS = ["gluten","dairy","egg","peanut","tree-nut","soy","shellfish","fish","sesame"];
const FLAVOURS  = ["spicy","sweet","sour","bitter","salty","umami","smoky","tangy","herby","garlicky","citrusy","creamy","rich","fresh"];
const TECHNIQUE = ["grill","roast","bake","fry","deep-fry","stir-fry","braise","stew","steam","poach","sous-vide","marinate","pickle","ferment"];
const COURSES   = ["breakfast","starter","main","side","dessert","drink","snack",null];

function recreate(name, validator) {
  if (appdb.getCollectionNames().includes(name)) appdb[name].drop();
  appdb.createCollection(name, { validator, validationLevel: "moderate" });
}

// kebab-case helper for schema patterns
const KEBAB = "^[a-z0-9]+(?:-[a-z0-9]+)*$";

recreate("recipes", {
  $jsonSchema: {
    bsonType: "object",
    required: ["title","ingredients","steps"],
    properties: {
      title: { bsonType: "string" },
      slug:  { bsonType: "string", pattern: KEBAB },
      ingredients: {
        bsonType: "array",
        items: {
          bsonType: "object",
          required: ["name","raw"],
          properties: {
            name: { bsonType: "string" },  // store lowercase canonical name
            qty:  { bsonType: ["double","int","string","null"] },
            unit: { bsonType: ["string","null"] },
            raw:  { bsonType: "string" }
          }
        }
      },
      steps: { bsonType: "array", items: { bsonType: "string" } },

      // freeform (kept for backward compat)
      tags: { bsonType: "array", items: { bsonType: "string" } },

      // ---- Structured tags (strict) ----
      dietary_tags:   { bsonType: "array", uniqueItems: true, items: { enum: DIETARY } },
      allergen_tags:  { bsonType: "array", uniqueItems: true, items: { enum: ALLERGENS } },
      flavour_tags:   { bsonType: "array", uniqueItems: true, items: { enum: FLAVOURS } },
      technique_tags: { bsonType: "array", uniqueItems: true, items: { enum: TECHNIQUE } },

      // ingredient tags = canonical, kebab-case, lowercase
      ingredient_tags:{ bsonType: "array", uniqueItems: true, items: { bsonType: "string", pattern: KEBAB } },

      // cuisine + course
      cuisine: { bsonType: ["string","null"], pattern: KEBAB },
      course:  { enum: COURSES },

      // provenance & classifiers
      tags_provenance: {
        bsonType: "object",
        properties: {
          version: { bsonType: "string" },
          methods: { bsonType: "array", items: { bsonType: "string" } }, // e.g., ["rules","llm","model"]
          ts:      { bsonType: "date" }
        }
      },
      cuisine_confidence: { bsonType: ["double","null"] },
      cuisine_method: {
        bsonType: "array",
        items: { enum: ["rules","model","llm"] }
      },

      author:  { bsonType: ["string","null"] },
      source_url: { bsonType: ["string","null"] },

      servings: { bsonType: ["int","null"] },
      times: {
        bsonType: "object",
        properties: {
          prep_min:  { bsonType: ["int","null"] },
          cook_min:  { bsonType: ["int","null"] },
          total_min: { bsonType: ["int","null"] }
        }
      },

      nutrition: { bsonType: "object", additionalProperties: true },

      rating: {
        bsonType: "object",
        properties: {
          value: { bsonType: ["double","int","null"] },
          count: { bsonType: ["int","null"] }
        }
      },

      images: {
        bsonType: "array",
        items: {
          bsonType: "object",
          properties: {
            url: { bsonType: "string" },
            attribution: { bsonType: ["string","null"] }
          }
        }
      },

      created_at: { bsonType: "date" },
      updated_at: { bsonType: "date" }
    }
  }
});
