"use client";

import { useState } from "react";
import Card from "@/components/horizon/Card";
import MiniStatistics from "@/components/horizon/MiniStatistics";
import { BranchSelector } from "./BranchSelector";
import { ProjectCharts } from "./ProjectCharts";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import { mockProjects, getProjectCopy, getProjectBranches } from "@/app/dashboard/mockData";
import { Users, GitBranch, TrendingUp, AlertTriangle } from "lucide-react";

interface ProjectDetailsProps {
  projectId?: string;
}

export function ProjectDetails({ projectId }: ProjectDetailsProps) {
  const [selectedBranch, setSelectedBranch] = useState("main");

  if (!projectId) {
    return (
      <Card>
        <div className="p-6">
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              {DASHBOARD_TEXT.NO_PROJECT_SELECTED}
            </p>
          </div>
        </div>
      </Card>
    );
  }

  const project = mockProjects.find(p => p.id === projectId);
  if (!project) {
    return (
      <Card>
        <div className="p-6">
          <div className="text-center py-12">
            <p className="text-destructive">
              Project not found
            </p>
          </div>
        </div>
      </Card>
    );
  }

  const projectCopy = getProjectCopy(projectId, selectedBranch);
  const branches = getProjectBranches(projectId);

  const handleBranchChange = (branchName: string) => {
    setSelectedBranch(branchName);
  };

  const handleCreateCopy = () => {
    // Mock creating a new branch copy
    console.log(`Creating copy for branch: ${selectedBranch}`);
  };

  return (
    <div className="space-y-6">
      {/* Project Header */}
      <Card>
        <div className="p-6">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-foreground">
              {project.name}
            </h2>
            <p className="text-muted-foreground mt-1">
              {project.description}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {project.repoUrl}
            </p>
          </div>
        </div>
      </Card>

      {/* Overview Statistics */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            {DASHBOARD_TEXT.TAB_OVERVIEW}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MiniStatistics
              name={DASHBOARD_TEXT.STAT_MEMBERS}
              value={projectCopy?.stats.memberCount.toString() || "0"}
              icon={<Users className="w-6 h-6" />}
              iconBg="bg-blue-100"
            />
            <MiniStatistics
              name={DASHBOARD_TEXT.STAT_BRANCHES}
              value={project.branches.length.toString()}
              icon={<GitBranch className="w-6 h-6" />}
              iconBg="bg-green-100"
            />
            <MiniStatistics
              name={DASHBOARD_TEXT.STAT_STC_SCORE}
              value={projectCopy?.stats.stcScore.toFixed(2) || "N/A"}
              icon={<TrendingUp className="w-6 h-6" />}
              iconBg="bg-purple-100"
            />
            <MiniStatistics
              name={DASHBOARD_TEXT.STAT_RISK_LEVEL}
              value={projectCopy?.stats.riskLevel || "Unknown"}
              icon={<AlertTriangle className="w-6 h-6" />}
              iconBg="bg-red-100"
            />
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Tabs Navigation */}
        <div className="lg:col-span-1">
          <Card>
            <div className="p-6">
              <nav className="space-y-2">
                {[
                  { id: 'overview', label: DASHBOARD_TEXT.TAB_OVERVIEW },
                  { id: 'members', label: DASHBOARD_TEXT.TAB_MEMBERS },
                  { id: 'branches', label: DASHBOARD_TEXT.TAB_BRANCHES },
                  { id: 'analytics', label: DASHBOARD_TEXT.TAB_ANALYTICS },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      // Tab switching logic would go here
                      console.log(`Switching to tab: ${tab.id}`);
                    }}
                    className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors text-sm font-medium text-navy-700 dark:text-white"
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </Card>
        </div>

        {/* Right Column - Tab Content */}
        <div className="lg:col-span-2">
          {/* Overview Tab */}
          <Card>
            <div className="p-6">
              <h4 className="text-lg font-semibold text-navy-700 dark:text-white mb-4">
                {DASHBOARD_TEXT.TAB_OVERVIEW}
              </h4>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {DASHBOARD_TEXT.BRANCH_SELECTOR_LABEL}
                    </label>
                    <select
                      value={selectedBranch}
                      onChange={(e) => handleBranchChange(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent dark:bg-navy-800 dark:border-gray-600 dark:text-white"
                    >
                      {branches.map((branch) => (
                        <option key={branch.name} value={branch.name}>
                          {branch.name} {branch.isCurrent ? "(Current)" : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleCreateCopy}
                      className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 text-sm font-medium transition-colors"
                    >
                      {DASHBOARD_TEXT.CREATE_COPY_BUTTON}
                    </button>
                  </div>
                </div>

                {projectCopy && (
                  <div className="mt-6">
                    <h5 className="text-md font-semibold text-navy-700 dark:text-white mb-3">
                      Team Members ({projectCopy.members.length})
                    </h5>
                    <div className="space-y-3">
                      {projectCopy.members.slice(0, 3).map((member) => (
                        <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-navy-700 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                              <span className="text-sm font-medium text-blue-600">
                                {member.name.charAt(0)}
                              </span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-navy-700 dark:text-white">
                                {member.name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {member.role}
                              </p>
                            </div>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Joined {new Date(member.joinedAt).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                      {projectCopy.members.length > 3 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                          +{projectCopy.members.length - 3} more members
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Charts */}
          <div className="mt-6">
            <ProjectCharts projectId={projectId} branchName={selectedBranch} />
          </div>
        </div>
      </div>
    </div>
  );
}

