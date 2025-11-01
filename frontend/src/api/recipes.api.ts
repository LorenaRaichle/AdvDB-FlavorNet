import { api } from "../utils/apiClient";

export const getTopRecipesByCuisine = (cuisine: string) =>
  api.get(`/recipes/top?cuisine=${cuisine}`);