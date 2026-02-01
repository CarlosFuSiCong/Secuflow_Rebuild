import { apiClient } from './client';
import type { ApiResponse } from '../types/response';

export interface CoordinationPair {
  id: string;
  contributor1_id: string;
  contributor1_role: string;
  contributor1_email: string;
  contributor2_id: string;
  contributor2_role: string;
  contributor2_email: string;
  coordination_requirement: number;
  actual_coordination: number;
  coordination_gap: number;
  impact_score: number;
  is_inter_class: boolean;
  is_missed_coordination: boolean;
  is_unnecessary_coordination: boolean;
  shared_files: string[];
  coordination_files: string[];
  coordination_type: string;
  coordination_status: string;
}

export interface CoordinationPairsResponse {
  analysis_id: string;
  coordination_pairs: CoordinationPair[];
  total_pairs: number;
}

export interface MCSTCResultsResponse {
  analysis_id: string;
  mcstc_value: number;
  inter_class_coordination_score: number;
  intra_class_coordination_score: number;
  role_coordination_matrix: Record<string, any>;
  top_coordination_pairs: Array<{
    contributor1: string;
    contributor2: string;
    coordination_requirement: number;
    actual_coordination: number;
    coordination_gap: number;
    impact_score: number;
    status: string;
  }>;
  recommendations: string[];
}

/**
 * Get detailed coordination pairs for an MC-STC analysis
 */
export async function getCoordinationPairs(
  analysisId: string,
  options?: {
    topN?: number;
    statusFilter?: 'missed' | 'unnecessary' | 'adequate';
    roleFilter?: 'developer' | 'security' | 'ops';
    interClassOnly?: boolean;
  }
): Promise<CoordinationPairsResponse> {
  const params = new URLSearchParams();
  if (options?.topN) params.append('top_n', options.topN.toString());
  if (options?.statusFilter) params.append('status_filter', options.statusFilter);
  if (options?.roleFilter) params.append('role_filter', options.roleFilter);
  if (options?.interClassOnly) params.append('inter_class_only', 'true');

  const queryString = params.toString();
  const url = `/mcstc/analyses/${analysisId}/coordination_pairs/${queryString ? '?' + queryString : ''}`;

  const { data } = await apiClient.get<ApiResponse<CoordinationPairsResponse>>(url);
  return data.data!;
}

/**
 * Get complete MC-STC analysis results
 */
export async function getMCSTCResults(
  analysisId: string,
  options?: {
    topN?: number;
    roleFilter?: string;
  }
): Promise<MCSTCResultsResponse> {
  const params = new URLSearchParams();
  if (options?.topN) params.append('top_n', options.topN.toString());
  if (options?.roleFilter) params.append('role_filter', options.roleFilter);

  const queryString = params.toString();
  const url = `/mcstc/analyses/${analysisId}/results/${queryString ? '?' + queryString : ''}`;

  const { data } = await apiClient.get<ApiResponse<MCSTCResultsResponse>>(url);
  return data.data!;
}
