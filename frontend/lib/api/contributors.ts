import { apiClient } from "./client";

export interface FunctionalRoleChoice {
  value: string;
  label: string;
}

export interface ProjectContributor {
  id: string;
  contributor_login: string;
  contributor_email: string;
  commits_count: number;
  total_modifications: number;
  files_modified: number;
  functional_role: string;
  functional_role_display: string;
  is_core_contributor: boolean;
  last_active_at: string;
}

export interface ContributorClassificationResponse {
  results: ProjectContributor[];
  count: number;
  next: string | null;
  previous: string | null;
}

export interface ContributorUpdate {
  id: string;
  functional_role?: string;
  is_core_contributor?: boolean;
}

/**
 * Get functional role choices
 */
export async function getFunctionalRoleChoices(): Promise<FunctionalRoleChoice[]> {
  const response = await apiClient.get("/contributors/functional-role-choices/");
  const choices = response.data.data.choices;
  
  // Backend returns an array of {value, label} objects directly
  return choices;
}

/**
 * Get project contributors for classification
 */
export async function getProjectContributorsClassification(
  projectId: string,
  params?: {
    page?: number;
    page_size?: number;
    role?: string;
    activity_level?: string;
    search?: string;
  }
): Promise<ContributorClassificationResponse> {
  const response = await apiClient.get(
    `/contributors/projects/${projectId}/classification/`,
    { params }
  );
  return response.data.data;
}

/**
 * Update contributor classifications (batch)
 */
export async function updateContributorClassifications(
  projectId: string,
  updates: ContributorUpdate[]
): Promise<{ updated_count: number }> {
  const response = await apiClient.patch(
    `/contributors/projects/${projectId}/classification/`,
    updates
  );
  return response.data.data;
}

/**
 * Trigger TNM contributor analysis
 */
export async function analyzeTNMContributors(
  projectId: string,
  options?: {
    tnm_output_dir?: string;
    branch?: string;
    async?: boolean;
  }
): Promise<any> {
  const response = await apiClient.post(
    `/contributors/projects/${projectId}/analyze_tnm/`,
    options || {}
  );
  return response.data;
}
