import Card from "@/components/horizon/Card";
import MiniStatistics from "@/components/horizon/MiniStatistics";
import { Users, GitBranch, TrendingUp, AlertTriangle } from "lucide-react";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectStatsProps } from "@/lib/types";

export function ProjectStats({ stats, branchesCount }: ProjectStatsProps) {
  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          {DASHBOARD_TEXT.TAB_OVERVIEW}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MiniStatistics
            name={DASHBOARD_TEXT.STAT_MEMBERS}
            value={stats.memberCount.toString()}
            icon={<Users className="w-6 h-6" />}
            iconBg="bg-blue-100 dark:bg-blue-900/20"
          />
          <MiniStatistics
            name={DASHBOARD_TEXT.STAT_BRANCHES}
            value={branchesCount.toString()}
            icon={<GitBranch className="w-6 h-6" />}
            iconBg="bg-green-100 dark:bg-green-900/20"
          />
          <MiniStatistics
            name={DASHBOARD_TEXT.STAT_STC_SCORE}
            value={stats.stcScore.toFixed(2)}
            icon={<TrendingUp className="w-6 h-6" />}
            iconBg="bg-purple-100 dark:bg-purple-900/20"
          />
          <MiniStatistics
            name={DASHBOARD_TEXT.STAT_RISK_LEVEL}
            value={stats.riskLevel}
            icon={<AlertTriangle className="w-6 h-6" />}
            iconBg="bg-red-100 dark:bg-red-900/20"
          />
        </div>
      </div>
    </Card>
  );
}
