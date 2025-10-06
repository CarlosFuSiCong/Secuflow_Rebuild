import type { AuthResponse } from "../types/auth";
import { apiClient } from "./client";

const persistTokens = (resp: AuthResponse) => {
  if (typeof window === "undefined") return;
  const payload = resp?.data;
  if (!payload) return;
  if (payload.access) localStorage.setItem("access_token", payload.access);
  if (payload.refresh) localStorage.setItem("refresh_token", payload.refresh);
  if (payload.user) localStorage.setItem("user", JSON.stringify(payload.user));
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

export async function logout() {
  if (typeof window === "undefined") return;

  const refreshToken = localStorage.getItem("refresh_token");

  // Call logout API if refresh token exists
  if (refreshToken) {
    try {
      await apiClient.post("/auth/logout/", {
        refresh: refreshToken,
      });
    } catch (error) {
      console.error("Logout API call failed:", error);
    }
  }

  // Clear tokens from localStorage
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getCurrentUser() {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}


