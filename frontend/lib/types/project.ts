import type { ApiResponse, PaginatedResult } from "./response";

// Branch information
export type Branch = {
  name: string;
  is_current: boolean;
  is_remote?: boolean;
  branch_id: string; // Required for branch switching
  commit_hash?: string;
};

// Validate repository response data (inside ApiResponse.data)
export type ValidateRepositoryData = {
  valid: boolean;
  branches: Branch[];
  default_branch: string;
  repo_url: string;
};

// API Response: Validate Repository
export type ValidateRepositoryResponse = ApiResponse<ValidateRepositoryData>;

// Create project request payload
export type CreateProjectRequest = {
  name: string;
  repo_url: string;
  description?: string;
  repo_type?: string;
  auto_run_stc?: boolean;
  auto_run_mcstc?: boolean;
};

// Repository info in create project response
export type RepositoryInfo = {
  branches: Branch[];
  current_branch: string;
  repository_path: string;
  used_authentication?: boolean;
};

// Create project response data (inside ApiResponse.data)
export type CreateProjectData = {
  id: string;
  name: string;
  repo_url: string;
  default_branch: string;
  repository_path?: string;
  owner_profile: number;
  owner_id: string;
  owner_username: string;
  owner_email: string;
  members_count: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  description?: string;
  repo_type?: string;
  stc_risk_score?: number;
  mcstc_risk_score?: number;
  last_risk_check_at?: string;
  latest_stc_result?: any;
  latest_mcstc_result?: any;
  available_branches?: string[];
  suggested_default_branch?: string;
  auto_run_stc?: boolean;
  auto_run_mcstc?: boolean;
};

// API Response: Create Project
export type CreateProjectResponse = ApiResponse<CreateProjectData>;

// List projects query parameters
export type ListProjectsParams = {
  q?: string;
  repo_type?: string;
  role?: string;
  sort?: string;
  include_deleted?: boolean;
  page?: number;
  page_size?: number;
};

// Project item in list
export type Project = {
  id: string;
  name: string;
  description?: string;
  repo_url: string;
  repo_type: string;
  default_branch?: string;
  repository_path?: string;
  owner_id: string;
  owner_username: string;
  members_count: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  stc_risk_score?: number;
  mcstc_risk_score?: number;
  last_risk_check_at?: string;
  latest_stc_result?: any;
  latest_mcstc_result?: any;
  auto_run_stc?: boolean;
  auto_run_mcstc?: boolean;
};

// API Response: List Projects (paginated)
export type ListProjectsResponse = PaginatedResult<Project>;
