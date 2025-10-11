import { apiClient } from "./client";
import type {
  Branch,
  ValidateRepositoryResponse,
  CreateProjectRequest,
  CreateProjectResponse,
  ListProjectsParams,
  Project,
  ListProjectsResponse,
} from "../types/project";
import type { ApiResponse } from "../types/response";

// Re-export types for backward compatibility
export type {
  Branch,
  ValidateRepositoryResponse,
  CreateProjectRequest,
  CreateProjectResponse,
  ListProjectsParams,
  Project,
  ListProjectsResponse,
};

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

export async function getProject(projectId: string): Promise<Project> {
  const { data } = await apiClient.get<ApiResponse<Project>>(
    `/projects/projects/${projectId}/`
  );
  if (!data.data) {
    throw new Error(data.errorMessage || "Failed to fetch project");
  }
  return data.data;
}

export interface BranchesResponse {
  branches: Branch[];
  current_branch: string;
  repository_path: string;
}

export async function getProjectBranches(projectId: string): Promise<BranchesResponse> {
  const { data } = await apiClient.get<ApiResponse<BranchesResponse>>(
    `/projects/projects/${projectId}/branches/`
  );
  if (!data.data) {
    throw new Error(data.errorMessage || "Failed to fetch project branches");
  }
  return data.data;
}
