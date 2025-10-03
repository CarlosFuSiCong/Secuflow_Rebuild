import type { ApiResponse } from "./response";
import type { User } from "./user";

export type AuthTokens = {
  refresh: string;
  access: string;
};

export type AuthPayload = AuthTokens & { user: User };

export type AuthResponse = ApiResponse<AuthPayload>;


