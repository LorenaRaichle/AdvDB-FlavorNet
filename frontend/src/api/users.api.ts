import { api } from "../utils/apiClient";

export const listUsers = () => api.get("/users");
export const getUserPrefs = (id: number) => api.get(`/users/${id}/prefs`);
export const updateUserPrefs = (id: number, data: any) =>
  api.put(`/users/${id}/prefs`, data);
export const clearUserPrefs = (id: number) =>
  api.delete(`/users/${id}/prefs`);
