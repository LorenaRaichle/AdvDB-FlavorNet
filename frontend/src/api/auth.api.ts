import { api } from "../utils/apiClient";

export const registerUser = (data: any) => api.post("/users", data);
// if you add login later in backend:
export const loginUser = (data: any) => api.post("/auth/login", data);
