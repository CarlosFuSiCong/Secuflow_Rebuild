// Dashboard component props and types

export interface ProjectListProps {
  selectedProjectId?: string;
  onProjectSelect?: (projectId: string) => void;
}

export interface ProjectChartsProps {
  projectId: string;
  branchName: string;
}

export interface ProjectDetailsProps {
  projectId?: string;
}

// Branch information for dashboard
export interface DashboardBranch {
  name: string;
  isCurrent: boolean;
  isRemote: boolean;
}

export interface BranchSelectorProps {
  branches: DashboardBranch[];
  selectedBranch?: string;
  onBranchChange?: (branchName: string) => void;
  onCreateCopy?: () => void;
}
