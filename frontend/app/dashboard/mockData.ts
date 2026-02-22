export interface ProjectCopy {
  id: string;
  projectId: string;
  branchName: string;
  stcData: Array<{ timestamp: string; value: number }>;
  members: Array<{
    id: string;
    name: string;
    email: string;
    role: string;
    joinedAt: string;
  }>;
  stats: {
    memberCount: number;
    stcScore: number;
    riskLevel: string;
  };
}

export interface Project {
  id: string;
  name: string;
  repoUrl: string;
  description?: string;
  createdAt: string;
  lastUpdated: string;
  branches: Array<{
    name: string;
    isCurrent: boolean;
    isRemote: boolean;
  }>;
  copies: ProjectCopy[];
}

export interface ChartDataPoint {
  x: string;
  y: number;
}

// Mock projects data
export const mockProjects: Project[] = [
  {
    id: "project-1",
    name: "E-commerce Platform",
    repoUrl: "https://github.com/company/ecommerce-platform",
    description: "Modern e-commerce platform with React and Node.js",
    createdAt: "2024-01-15",
    lastUpdated: "2024-12-09",
    branches: [
      { name: "main", isCurrent: true, isRemote: false },
      { name: "develop", isCurrent: false, isRemote: false },
      { name: "feature/user-auth", isCurrent: false, isRemote: false },
      { name: "hotfix/payment-bug", isCurrent: false, isRemote: false },
      { name: "origin/main", isCurrent: false, isRemote: true },
    ],
    copies: [
      {
        id: "copy-1",
        projectId: "project-1",
        branchName: "main",
        stcData: [
          { timestamp: "2024-01-15", value: 0.85 },
          { timestamp: "2024-02-15", value: 0.82 },
          { timestamp: "2024-03-15", value: 0.88 },
          { timestamp: "2024-04-15", value: 0.91 },
          { timestamp: "2024-05-15", value: 0.89 },
          { timestamp: "2024-06-15", value: 0.87 },
          { timestamp: "2024-07-15", value: 0.90 },
          { timestamp: "2024-08-15", value: 0.92 },
          { timestamp: "2024-09-15", value: 0.94 },
          { timestamp: "2024-10-15", value: 0.93 },
          { timestamp: "2024-11-15", value: 0.95 },
          { timestamp: "2024-12-09", value: 0.96 },
        ],
        members: [
          { id: "1", name: "Alice Johnson", email: "alice@company.com", role: "Lead Developer", joinedAt: "2024-01-15" },
          { id: "2", name: "Bob Smith", email: "bob@company.com", role: "Frontend Developer", joinedAt: "2024-01-16" },
          { id: "3", name: "Carol Williams", email: "carol@company.com", role: "Backend Developer", joinedAt: "2024-01-17" },
          { id: "4", name: "David Brown", email: "david@company.com", role: "UI/UX Designer", joinedAt: "2024-01-18" },
        ],
        stats: {
          memberCount: 4,
          stcScore: 0.96,
          riskLevel: "Low",
        },
      },
      {
        id: "copy-2",
        projectId: "project-1",
        branchName: "develop",
        stcData: [
          { timestamp: "2024-01-15", value: 0.78 },
          { timestamp: "2024-02-15", value: 0.75 },
          { timestamp: "2024-03-15", value: 0.80 },
          { timestamp: "2024-04-15", value: 0.83 },
          { timestamp: "2024-05-15", value: 0.85 },
          { timestamp: "2024-06-15", value: 0.82 },
          { timestamp: "2024-07-15", value: 0.86 },
          { timestamp: "2024-08-15", value: 0.88 },
          { timestamp: "2024-09-15", value: 0.90 },
          { timestamp: "2024-10-15", value: 0.89 },
          { timestamp: "2024-11-15", value: 0.91 },
          { timestamp: "2024-12-09", value: 0.93 },
        ],
        members: [
          { id: "1", name: "Alice Johnson", email: "alice@company.com", role: "Lead Developer", joinedAt: "2024-01-15" },
          { id: "2", name: "Bob Smith", email: "bob@company.com", role: "Frontend Developer", joinedAt: "2024-01-16" },
          { id: "5", name: "Eve Davis", email: "eve@company.com", role: "QA Engineer", joinedAt: "2024-02-01" },
        ],
        stats: {
          memberCount: 3,
          stcScore: 0.93,
          riskLevel: "Medium",
        },
      },
    ],
  },
  {
    id: "project-2",
    name: "Mobile App",
    repoUrl: "https://github.com/company/mobile-app",
    description: "React Native mobile application",
    createdAt: "2024-03-01",
    lastUpdated: "2024-12-08",
    branches: [
      { name: "main", isCurrent: true, isRemote: false },
      { name: "feature/push-notifications", isCurrent: false, isRemote: false },
      { name: "origin/main", isCurrent: false, isRemote: true },
    ],
    copies: [
      {
        id: "copy-3",
        projectId: "project-2",
        branchName: "main",
        stcData: [
          { timestamp: "2024-03-01", value: 0.92 },
          { timestamp: "2024-04-01", value: 0.89 },
          { timestamp: "2024-05-01", value: 0.91 },
          { timestamp: "2024-06-01", value: 0.94 },
          { timestamp: "2024-07-01", value: 0.93 },
          { timestamp: "2024-08-01", value: 0.95 },
          { timestamp: "2024-09-01", value: 0.96 },
          { timestamp: "2024-10-01", value: 0.97 },
          { timestamp: "2024-11-01", value: 0.98 },
          { timestamp: "2024-12-08", value: 0.99 },
        ],
        members: [
          { id: "6", name: "Frank Miller", email: "frank@company.com", role: "Mobile Developer", joinedAt: "2024-03-01" },
          { id: "7", name: "Grace Lee", email: "grace@company.com", role: "Product Manager", joinedAt: "2024-03-02" },
        ],
        stats: {
          memberCount: 2,
          stcScore: 0.99,
          riskLevel: "Low",
        },
      },
    ],
  },
  {
    id: "project-3",
    name: "Data Analytics Platform",
    repoUrl: "https://github.com/company/data-analytics",
    description: "Big data analytics and visualization platform",
    createdAt: "2024-06-01",
    lastUpdated: "2024-12-07",
    branches: [
      { name: "main", isCurrent: true, isRemote: false },
      { name: "feature/ml-models", isCurrent: false, isRemote: false },
      { name: "origin/main", isCurrent: false, isRemote: true },
    ],
    copies: [
      {
        id: "copy-4",
        projectId: "project-3",
        branchName: "main",
        stcData: [
          { timestamp: "2024-06-01", value: 0.76 },
          { timestamp: "2024-07-01", value: 0.74 },
          { timestamp: "2024-08-01", value: 0.78 },
          { timestamp: "2024-09-01", value: 0.81 },
          { timestamp: "2024-10-01", value: 0.83 },
          { timestamp: "2024-11-01", value: 0.85 },
          { timestamp: "2024-12-07", value: 0.87 },
        ],
        members: [
          { id: "8", name: "Henry Wilson", email: "henry@company.com", role: "Data Scientist", joinedAt: "2024-06-01" },
          { id: "9", name: "Ivy Chen", email: "ivy@company.com", role: "Data Engineer", joinedAt: "2024-06-02" },
          { id: "10", name: "Jack Taylor", email: "jack@company.com", role: "ML Engineer", joinedAt: "2024-06-03" },
        ],
        stats: {
          memberCount: 3,
          stcScore: 0.87,
          riskLevel: "Medium",
        },
      },
    ],
  },
];

// Helper function to get project copy by project and branch
export function getProjectCopy(projectId: string, branchName: string): ProjectCopy | undefined {
  const project = mockProjects.find(p => p.id === projectId);
  if (!project) return undefined;
  return project.copies.find(copy => copy.branchName === branchName);
}

// Helper function to get all branches for a project
export function getProjectBranches(projectId: string) {
  const project = mockProjects.find(p => p.id === projectId);
  return project?.branches || [];
}

// Chart data helpers
export function getSTCTrendData(projectId: string, branchName: string): ChartDataPoint[] {
  const copy = getProjectCopy(projectId, branchName);
  if (!copy) return [];

  return copy.stcData.map(point => ({
    x: point.timestamp,
    y: point.value,
  }));
}

export function getCoordinationData(_projectId: string, _branchName: string) {
  // Mock coordination data
  return [
    { x: "Alice & Bob", y: 0.8 },
    { x: "Alice & Carol", y: 0.6 },
    { x: "Bob & Carol", y: 0.9 },
    { x: "Alice & David", y: 0.7 },
    { x: "Bob & David", y: 0.5 },
  ];
}

export function getRoleDistributionData(projectId: string, branchName: string) {
  const copy = getProjectCopy(projectId, branchName);
  if (!copy) return [];

  const roleCounts = copy.members.reduce((acc, member) => {
    acc[member.role] = (acc[member.role] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(roleCounts).map(([role, count]) => ({
    x: role,
    y: count,
  }));
}

