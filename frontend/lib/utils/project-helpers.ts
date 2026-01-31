/**
 * Project-related utility functions for data transformation and calculations
 */

import type { Project } from "../types/project";

/**
 * Calculate risk level based on risk score
 * Risk score ranges from 0 to 1, where higher values indicate higher risk
 * @param riskScore - The risk score (0-1)
 * @returns Risk level: "High", "Medium", or "Low"
 */
export function getRiskLevel(riskScore: number | undefined | null): "High" | "Medium" | "Low" {
  if (riskScore === undefined || riskScore === null) {
    return "High"; // Default to high risk if no score available
  }
  
  if (riskScore >= 0.7) return "High";
  if (riskScore >= 0.4) return "Medium";
  return "Low";
}

/**
 * Get STC score from project data
 * STC value = 1 - risk_score (since risk_score = 1 - stc_value)
 * @param project - Project data from API
 * @returns STC score (0-1) or null if not available
 */
export function getStcScore(project: Project): number | null {
  if (project.stc_risk_score !== undefined && project.stc_risk_score !== null) {
    return 1 - project.stc_risk_score;
  }
  return null;
}

/**
 * Get MC-STC score from project data
 * MC-STC value = 1 - mcstc_risk_score
 * @param project - Project data from API
 * @returns MC-STC score (0-1) or null if not available
 */
export function getMcStcScore(project: Project): number | null {
  if (project.mcstc_risk_score !== undefined && project.mcstc_risk_score !== null) {
    return 1 - project.mcstc_risk_score;
  }
  return null;
}

/**
 * Format date string to locale date string
 * @param dateString - ISO date string
 * @returns Formatted date string
 */
export function formatProjectDate(dateString: string): string {
  try {
    return new Date(dateString).toLocaleDateString();
  } catch {
    return dateString;
  }
}

/**
 * Enhanced project interface for dashboard display
 * Combines API data with calculated fields
 */
export interface EnhancedProject extends Project {
  branchCount?: number;
  riskLevel: "High" | "Medium" | "Low";
  stcScore: number | null;
  mcStcScore: number | null;
}

/**
 * Transform API project data to enhanced project for dashboard
 * @param project - Project data from API
 * @param branchCount - Optional branch count (fetched separately)
 * @returns Enhanced project with calculated fields
 */
export function enhanceProject(project: Project, branchCount?: number): EnhancedProject {
  return {
    ...project,
    branchCount,
    riskLevel: getRiskLevel(project.stc_risk_score),
    stcScore: getStcScore(project),
    mcStcScore: getMcStcScore(project),
  };
}

