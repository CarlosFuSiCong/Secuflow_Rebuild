"use client";

import { useState } from "react";
import Card from "@/components/horizon/Card";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import { mockProjects, Project } from "@/app/dashboard/mockData";

interface ProjectListProps {
  selectedProjectId?: string;
  onProjectSelect?: (projectId: string) => void;
}

export function ProjectList({ selectedProjectId, onProjectSelect }: ProjectListProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredProjects = mockProjects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.repoUrl.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case "High":
        return "bg-red-100 text-red-800";
      case "Medium":
        return "bg-yellow-100 text-yellow-800";
      case "Low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <Card extra="h-full">
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-foreground mb-4">
            {DASHBOARD_TEXT.PROJECT_LIST_TITLE}
          </h3>

          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              placeholder={DASHBOARD_TEXT.PROJECT_SEARCH_PLACEHOLDER}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent bg-background text-foreground"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Project List */}
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {filteredProjects.map((project) => {
            const currentCopy = project.copies.find(copy => copy.branchName === "main");
            const isSelected = selectedProjectId === project.id;

            return (
              <div
                key={project.id}
                onClick={() => onProjectSelect?.(project.id)}
                className={`p-4 rounded-lg cursor-pointer transition-all duration-200 border ${
                  isSelected
                    ? "bg-primary/5 border-primary"
                    : "bg-card border-border hover:bg-accent"
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-foreground text-sm">
                      {project.name}
                    </h4>
                    <p className="text-xs text-muted-foreground truncate mt-1">
                      {project.repoUrl}
                    </p>
                  </div>
                  {currentCopy && (
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskBadgeVariant(currentCopy.stats.riskLevel)}`}>
                      {currentCopy.stats.riskLevel}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <div className="flex items-center space-x-4">
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      {currentCopy?.stats.memberCount || 0}
                    </span>
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                      </svg>
                      {project.branches.length}
                    </span>
                  </div>
                  <span className="font-medium text-primary">
                    STC: {currentCopy?.stats.stcScore.toFixed(2) || "N/A"}
                  </span>
                </div>
              </div>
            );
          })}

          {filteredProjects.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              {DASHBOARD_TEXT.MSG_NO_DATA}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

