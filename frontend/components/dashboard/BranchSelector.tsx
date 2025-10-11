"use client";

import { useState } from "react";
import Card from "@/components/horizon/Card";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { BranchSelectorProps, DashboardBranch } from "@/lib/types";

export function BranchSelector({
  branches,
  selectedBranch = "main",
  onBranchChange,
  onCreateCopy
}: BranchSelectorProps) {
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateCopy = async () => {
    setIsCreating(true);
    try {
      // Mock API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      onCreateCopy?.();
    } catch (error) {
      console.error("Failed to create branch copy:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const getBranchTypeLabel = (isRemote: boolean) => {
    return isRemote ? DASHBOARD_TEXT.BRANCH_REMOTE : DASHBOARD_TEXT.BRANCH_LOCAL;
  };

  const getBranchBadgeVariant = (isCurrent: boolean, isRemote: boolean) => {
    if (isCurrent) return "bg-green-100 text-green-800";
    if (isRemote) return "bg-blue-100 text-blue-800";
    return "bg-muted text-muted-foreground";
  };

  return (
    <Card>
      <div className="p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-navy-700 dark:text-white">
              {DASHBOARD_TEXT.TAB_BRANCHES}
            </h4>
            <button
              onClick={handleCreateCopy}
              disabled={isCreating}
              className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
            >
              {isCreating ? DASHBOARD_TEXT.MSG_LOADING : DASHBOARD_TEXT.CREATE_COPY_BUTTON}
            </button>
          </div>

          {/* Current Branch Info */}
          <div className="mb-4 p-3 bg-gray-50 dark:bg-navy-700 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  {DASHBOARD_TEXT.BRANCH_CURRENT_LABEL}
                </p>
                <p className="text-sm font-semibold text-navy-700 dark:text-white">
                  {selectedBranch}
                </p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                {DASHBOARD_TEXT.BRANCH_CURRENT}
              </span>
            </div>
          </div>
        </div>

        {/* Available Branches */}
        <div>
          <h5 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">
            {DASHBOARD_TEXT.BRANCH_AVAILABLE_BRANCHES} ({branches.length})
          </h5>

          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {branches.map((branch) => (
              <div
                key={branch.name}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  branch.name === selectedBranch
                    ? "bg-brand-50 border-brand-200 dark:bg-brand-900/20 dark:border-brand-700"
                    : "bg-white border-gray-200 hover:bg-gray-50 dark:bg-navy-800 dark:border-gray-700 dark:hover:bg-navy-700"
                }`}
                onClick={() => onBranchChange?.(branch.name)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                      </svg>
                      <span className="font-medium text-navy-700 dark:text-white text-sm">
                        {branch.name}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {getBranchTypeLabel(branch.isRemote)}
                    </p>
                  </div>

                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getBranchBadgeVariant(branch.isCurrent, branch.isRemote)}`}>
                    {branch.isCurrent ? DASHBOARD_TEXT.BRANCH_CURRENT : getBranchTypeLabel(branch.isRemote)}
                  </span>
                </div>
              </div>
            ))}

            {branches.length === 0 && (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                {DASHBOARD_TEXT.MSG_NO_DATA}
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

