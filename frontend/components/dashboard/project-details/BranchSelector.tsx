import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectDetailsBranchSelectorProps } from "@/lib/types";

export function BranchSelector({
  selectedBranch,
  branches,
  onBranchChange
}: ProjectDetailsBranchSelectorProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-foreground mb-2">
        {DASHBOARD_TEXT.BRANCH_SELECTOR_LABEL}
      </label>
      <select
        value={selectedBranch}
        onChange={(e) => onBranchChange(e.target.value)}
        className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent bg-background text-foreground"
      >
        {branches.map((branch) => (
          <option key={branch.name} value={branch.name}>
            {branch.name} {branch.is_current ? "(Current)" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
