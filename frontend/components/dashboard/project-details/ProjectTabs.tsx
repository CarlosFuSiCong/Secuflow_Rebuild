import Card from "@/components/horizon/Card";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectTabsProps } from "@/lib/types";

const TABS = [
  { id: 'overview', label: DASHBOARD_TEXT.TAB_OVERVIEW },
  { id: 'members', label: DASHBOARD_TEXT.TAB_MEMBERS },
  { id: 'branches', label: DASHBOARD_TEXT.TAB_BRANCHES },
  { id: 'analytics', label: DASHBOARD_TEXT.TAB_ANALYTICS },
];

export function ProjectTabs({ activeTab = 'overview', onTabChange }: ProjectTabsProps) {
  const handleTabClick = (tabId: string) => {
    if (onTabChange) {
      onTabChange(tabId);
    }
  };

  return (
    <Card>
      <div className="p-6">
        <nav className="space-y-2">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`w-full text-left px-4 py-3 rounded-lg hover:bg-accent transition-colors text-sm font-medium ${
                activeTab === tab.id
                  ? 'bg-accent text-foreground'
                  : 'text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </Card>
  );
}
