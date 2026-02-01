import { apiClient } from './client';
import type { ApiResponse } from '../types/response';

export interface STCResult {
  analysis_id: string;
  project_id: string;
  analysis_date: string;
  use_monte_carlo: boolean;
  results: {
    stc_value: number;
    coordination_requirements_total: number;
    coordination_actuals_total: number;
    missed_coordination_count: number;
    unnecessary_coordination_count: number;
    contributors_count: number;
    files_count: number;
    branch_analyzed: string;
    coordination_efficiency: number;
  };
}

/**
 * Get STC analysis results
 */
export async function getSTCResults(analysisId: string): Promise<STCResult> {
  const { data } = await apiClient.get<ApiResponse<STCResult>>(
    `/stc/analyses/${analysisId}/results/`
  );
  return data.data!;
}

export interface STCMatrixResponse {
  analysis_id: string;
  matrix: number[][];
  contributors: string[];
  stc_value: number;
}

export async function getLatestSTCAnalysis(projectId: string): Promise<any> {
  const { data } = await apiClient.get<ApiResponse<any>>(
    `/stc/analyses/?project_id=${projectId}`
  );
  if (!data.data || !data.data.results || data.data.results.length === 0) {
    throw new Error("No STC analysis found for this project");
  }
  return data.data.results[0]; // Return the most recent analysis
}

export async function getSTCMatrix(analysisId: string): Promise<STCMatrixResponse> {
  const { data } = await apiClient.get<ApiResponse<STCMatrixResponse>>(
    `/stc/analyses/${analysisId}/matrix/`
  );
  return data.data!;
}

export async function triggerSTCAnalysis(
  projectId: string,
  branch: string,
  tnmOutputDir: string
): Promise<{ analysis_id: string }> {
  const response = await apiClient.post(`/stc/analyses/`, {
    project: projectId,
    branch,
    tnm_output_dir: tnmOutputDir
  });
  return response.data.data;
}

export async function triggerMCSTCAnalysis(
  projectId: string,
  branch: string,
  tnmOutputDir: string
): Promise<{ analysis_id: string }> {
  const response = await apiClient.post(`/mcstc/analyses/`, {
    project: projectId,
    branch,
    tnm_output_dir: tnmOutputDir,
    monte_carlo_iterations: 1000,
    functional_roles_used: ['developer', 'security', 'ops']
  });
  return response.data.data;
}
