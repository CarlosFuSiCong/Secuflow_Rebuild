import { apiClient } from "./client";
import type { ApiResponse } from "../types/response";
import type { STCMatrixResponse } from "../types/stc";

export async function getSTCMatrix(analysisId: string): Promise<STCMatrixResponse> {
  const { data } = await apiClient.get<ApiResponse<STCMatrixResponse>>(
    `/stc_analysis/analyses/${analysisId}/matrix/`
  );
  
  if (!data.data) {
    throw new Error(data.errorMessage || "Failed to fetch STC matrix");
  }
  
  return data.data;
}
