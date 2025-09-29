// Standardized API response types aligned with backend/common/response.py

export interface ApiResponse<T = unknown> {
  succeed: boolean;
  message?: string | null;
  errorMessage?: string | null;
  errorCode?: string | null;
  data?: T;
}

export interface PaginatedResult<T = unknown> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}

export type ApiPaginatedResponse<T = unknown> = ApiResponse<PaginatedResult<T>>;


