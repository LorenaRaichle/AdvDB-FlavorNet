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
            qty: { bsonType: ["double","int","string","null"] },
            unit:{ bsonType: ["string","null"] },
            raw: { bsonType: "string" }
          }
        }
      },
      steps: { bsonType: "array", items: { bsonType: "string" } },
      tags: { bsonType: "array", items: { bsonType: "string" } },
      cuisine: { bsonType: ["string","null"] },
      author: { bsonType: ["string","null"] },
      source_url: { bsonType: ["string","null"] },
      servings: { bsonType: ["int","null"] },
      times: {
        bsonType: "object",
        properties: {
          prep_min: { bsonType: ["int","null"] },
          cook_min: { bsonType: ["int","null"] },
          total_min:{ bsonType: ["int","null"] }
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
      created_at: { bsonType: "date" },
      updated_at: { bsonType: "date" }
    }
  }
});

// comments
recreate("comments", {
  $jsonSchema: {
    bsonType: "object",
    required: ["recipe_id","author","text","created_at"],
    properties: {
      recipe_id: { bsonType: ["objectId","int","string"] },
      author: { bsonType: "string" },
      text: { bsonType: "string" },
      created_at: { bsonType: "date" }
    }
  }
});

// users_public
recreate("users_public", {
  $jsonSchema: {
    bsonType: "object",
    required: ["user_id","username","created_at"],
    properties: {
      user_id: { bsonType: ["int","string"] },
      username: { bsonType: "string" },
      avatar_url: { bsonType: ["string","null"] },
      prefs: { bsonType: "object", additionalProperties: true },
      created_at: { bsonType: "date" }
    }
  }
});

print(`Created DB '${DB_NAME}' with collections:`, appdb.getCollectionNames());
