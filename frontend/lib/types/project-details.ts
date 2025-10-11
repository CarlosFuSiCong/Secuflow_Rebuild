import type { Project, Branch } from "./project";

export interface ProjectMember {
  id: string;
  name: string;
  role: string;
  joinedAt: string;
}

export interface ProjectStats {
  memberCount: number;
  stcScore: number;
  riskLevel: string;
}

export interface ProjectCopy {
  id: string;
  projectId: string;
  branchName: string;
  stcData: any[];
  members: ProjectMember[];
  stats: ProjectStats;
}

export interface ProjectHeaderProps {
  project: Project;
}

export interface ProjectStatsProps {
  stats: ProjectStats;
  branchesCount: number;
}

export interface ProjectDetailsBranchSelectorProps {
  selectedBranch: string;
  branches: Branch[];
  onBranchChange: (branchName: string) => void;
}

export interface TeamMembersListProps {
  members: ProjectMember[];
  maxDisplay?: number;
  projectId?: string;
  onMemberAdded?: () => void;
}

export interface ProjectTabsProps {
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
}

export interface EmptyStateProps {
  message: string;
}

export interface LoadingStateProps {
  message?: string;
}

export interface ErrorStateProps {
  error: string;
}

// AddMembers component types
export interface AddMemberRequest {
  user_id: string;
  role: string;
}

export interface AddMembersProps {
  projectId: string;
  existingMembers?: ProjectMember[];
  onMemberAdded?: () => void;
}
