import type { UpdateProfilePayload, User } from "../types/user";
import type { ApiResponse } from "../types/response";
import { apiClient } from "./client";

export async function updateProfile(payload: UpdateProfilePayload) {
  if (payload.avatar instanceof Blob) {
    const form = new FormData();
    if (payload.contact_email !== undefined) form.append("contact_email", String(payload.contact_email));
    if (payload.first_name !== undefined) form.append("first_name", String(payload.first_name));
    if (payload.last_name !== undefined) form.append("last_name", String(payload.last_name));
    form.append("avatar", payload.avatar);
    const { data } = await apiClient.patch("/users/update_profile/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }

  const body: Record<string, any> = {};
  if (payload.contact_email !== undefined) body.contact_email = payload.contact_email;
  if (payload.first_name !== undefined) body.first_name = payload.first_name;
  if (payload.last_name !== undefined) body.last_name = payload.last_name;
  const { data } = await apiClient.patch("/users/update_profile/", body);
  return data;
}

export async function changePassword(oldPassword: string, newPassword: string, newPasswordConfirm: string) {
  const { data } = await apiClient.post("/users/change_password/", {
    old_password: oldPassword,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm,
  });
  return data;
}

export async function fetchCurrentUser(): Promise<ApiResponse<User>> {
  const { data } = await apiClient.get<ApiResponse<User>>("/users/me/");
  return data;
}

export interface SearchUsersParams {
  search?: string;
  page?: number;
  page_size?: number;
}

export interface SearchUsersResponse {
  results: User[];
  count: number;
  next: string | null;
  previous: string | null;
}

export async function searchUsers(params: SearchUsersParams = {}): Promise<ApiResponse<SearchUsersResponse>> {
  const queryParams = new URLSearchParams();

  if (params.search) queryParams.append('search', params.search);
  if (params.page) queryParams.append('page', String(params.page));
  if (params.page_size) queryParams.append('page_size', String(params.page_size));

  const { data } = await apiClient.get<ApiResponse<SearchUsersResponse>>(
    `/users/?${queryParams.toString()}`
  );
  return data;
}


