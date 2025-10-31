// 01_collections.js
// Run with: mongosh --file 01_collections.js --eval "DB_NAME='appdb'"

const DB_NAME = (typeof DB_NAME !== 'undefined') ? DB_NAME : 'appdb';

const appdb = db.getSiblingDB(DB_NAME);

// Drop & (re)create collections with validators
function recreate(name, validator) {
  if (appdb.getCollectionNames().includes(name)) appdb[name].drop();
  appdb.createCollection(name, { validator, validationLevel: "moderate" });
}



// recipes
recreate("recipes", {
  $jsonSchema: {
    bsonType: "object",
    required: ["title", "ingredients", "steps"],
    properties: {
      title: { bsonType: "string" },
      slug: { bsonType: "string" },
      ingredients: {
        bsonType: "array",
        items: {
          bsonType: "object",
          required: ["name","raw"],
          properties: {
            name: { bsonType: "string" },
            qty:  { bsonType: ["double","int","string","null"] },
            unit: { bsonType: ["string","null"] },
            raw:  { bsonType: "string" }
          }
        }
      },
      steps: { bsonType: "array", items: { bsonType: "string" } },

      // catch-all tags s
      tags: { bsonType: "array", items: { bsonType: "string" } },

      // structured tag fields
      dietary_tags:   { bsonType: "array", items: { bsonType: "string" } }, // e.g., vegan, vegetarian, gluten-free
      flavour_tags:   { bsonType: "array", items: { bsonType: "string" } }, // e.g., spicy, smoky, sweet
      ingredient_tags:{ bsonType: "array", items: { bsonType: "string" } }, // deduped ingredient names

      cuisine: { bsonType: ["string","null"] },
      course:  { bsonType: ["string","null"] }, // breakfast, main, dessert, etc.
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

      // image metadata
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
