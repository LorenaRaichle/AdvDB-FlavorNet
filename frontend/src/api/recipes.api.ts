import { api } from "../utils/apiClient";

export const getRecommendedRecipes = (userId: number, limit = 12) =>
  api.get("/recipes/recommended", {
    params: { user_id: userId, limit },
  });

export const searchRecipes = (
  userId: number,
  query: string,
  limit = 12
) =>
  api.get("/recipes/search", {
    params: { user_id: userId, query, limit },
  });
