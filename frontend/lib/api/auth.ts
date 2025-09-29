import type { AuthResponse } from "../types/auth";
import { apiClient } from "./client";

const persistTokens = (resp: AuthResponse) => {
  if (typeof window === "undefined") return;
  const payload = resp?.data;
  if (!payload) return;
  if (payload.access) localStorage.setItem("access_token", payload.access);
  if (payload.refresh) localStorage.setItem("refresh_token", payload.refresh);
};

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login/", { email, password });
  persistTokens(data);
  return data;
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/register/", {
    email,
    password,
    password_confirm: password,
  });
  persistTokens(data);
  return data;
}

export function logout() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}


