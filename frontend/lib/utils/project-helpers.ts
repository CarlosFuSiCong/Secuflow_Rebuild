/**
 * Project-related utility functions for data transformation and calculations
 */

import type { Project } from "../types/project";

/**
 * Get score label based on score value (higher score = better coordination).
 * @param score - The STC/MC-STC score (0-1, higher = better)
 * @returns Label: "Good", "Fair", or "Poor"
 */
export function getRiskLevel(score: number | undefined | null): "Good" | "Fair" | "Poor" {
  if (score === undefined || score === null) return "Poor";
  if (score > 0.7) return "Good";
  if (score > 0.3) return "Fair";
  return "Poor";
}

/**
 * Get STC score from project data.
 * stc_risk_score IS the coordination score (0–1, higher = better).
 */
export function getStcScore(project: Project): number | null {
  return project.stc_risk_score ?? null;
}

/**
 * Get MC-STC score from project data.
 * mcstc_risk_score IS the coordination score (0–1, higher = better).
 */
export function getMcStcScore(project: Project): number | null {
  return project.mcstc_risk_score ?? null;
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
  riskLevel: "Good" | "Fair" | "Poor";
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

