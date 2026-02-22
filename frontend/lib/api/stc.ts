import { apiClient } from './client';
import type { ApiResponse } from '../types/response';
import type { STCMatrixResponse } from '../types/stc';

export type { STCMatrixResponse };

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
  // Step 1: create the analysis record
  const createResp = await apiClient.post(`/stc/analyses/`, {
    project: projectId,
  });
  const analysisId: string = createResp.data.data.id;

  // Step 2: run the calculation
  const startResp = await apiClient.post(`/stc/analyses/${analysisId}/start_analysis/`, {
    branch,
    tnm_output_dir: tnmOutputDir,
  });
  return { analysis_id: analysisId, ...startResp.data.data };
}

export async function triggerMCSTCAnalysis(
  projectId: string,
  branch: string,
  tnmOutputDir: string
): Promise<{ analysis_id: string }> {
  // Step 1: create the MC-STC analysis record
  const createResp = await apiClient.post(`/mcstc/analyses/`, {
    project: projectId,
    monte_carlo_iterations: 1000,
    functional_roles_used: ['developer', 'security', 'ops'],
  });
  const analysisId: string = createResp.data.data.id;

  // Step 2: run the calculation
  const startResp = await apiClient.post(`/mcstc/analyses/${analysisId}/start_analysis/`, {
    branch,
    tnm_output_dir: tnmOutputDir,
  });
  return { analysis_id: analysisId, ...startResp.data.data };
}
