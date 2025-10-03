import { apiClient } from "./client";

export interface Branch {
  name: string;
  is_current: boolean;
}

export interface ValidateRepositoryResponse {
  data: {
    valid: boolean;
    repo_name?: string;
    repo_description?: string;
    repo_owner?: string;
    default_branch?: string;
    branches?: Branch[];
    stars?: number;
    repo_url?: string;
    [key: string]: any;
  };
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  repo_url: string;
  repo_type: string;
}

export interface CreateProjectResponse {
  data: {
    id: number;
    name: string;
    repo_url: string;
    branch: string;
    [key: string]: any;
  };
}

export async function validateRepository(repoUrl: string): Promise<ValidateRepositoryResponse> {
  const { data } = await apiClient.post<ValidateRepositoryResponse>(
    "/projects/projects/validate_repository/",
    { repo_url: repoUrl }
  );
  return data;
}

export async function createProject(request: CreateProjectRequest): Promise<CreateProjectResponse> {
  const { data } = await apiClient.post<CreateProjectResponse>("/projects/projects/", request);
  return data;
}

export interface ListProjectsParams {
  q?: string;
  repo_type?: string;
  role?: string;
  sort?: string;
  include_deleted?: boolean;
  page?: number;
  page_size?: number;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  repo_url: string;
  repo_type: string;
  default_branch?: string;
  owner_id: string;
  owner_username: string;
  owner_email: string;
  members_count: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  stc_risk_score?: number;
  mcstc_risk_score?: number;
  last_risk_check_at?: string;
}

export interface ListProjectsResponse {
  results: Project[];
  count: number;
  next: string | null;
  previous: string | null;
}

export async function listProjects(params: ListProjectsParams = {}): Promise<ListProjectsResponse> {
  const queryParams = new URLSearchParams();

  if (params.q) queryParams.append('q', params.q);
  if (params.repo_type) queryParams.append('repo_type', params.repo_type);
  if (params.role) queryParams.append('role', params.role);
  if (params.sort) queryParams.append('sort', params.sort);
  if (params.include_deleted !== undefined) queryParams.append('include_deleted', String(params.include_deleted));
  if (params.page) queryParams.append('page', String(params.page));
  if (params.page_size) queryParams.append('page_size', String(params.page_size));

  const { data } = await apiClient.get<ListProjectsResponse>(
    `/projects/projects/?${queryParams.toString()}`
  );
  return data;
}
