"use client";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Branch } from "@/lib/api/projects";

const TEXT = {
  LABEL_BRANCH: "Select Branch",
  BRANCH_PLACEHOLDER: "Select a branch",
};

interface BranchSelectorProps {
  branches: Branch[];
  selectedBranch: string;
  defaultBranch?: string;
  onBranchChange: (value: string) => void;
  disabled?: boolean;
}

export function BranchSelector({
  branches,
  selectedBranch,
  defaultBranch,
  onBranchChange,
  disabled = false,
}: BranchSelectorProps) {
  if (!branches || branches.length === 0) {
    return null;
  }

  return (
    <div className="space-y-20">
      <Label htmlFor="branch-select">{TEXT.LABEL_BRANCH}</Label>
      <Select
        value={selectedBranch}
        onValueChange={onBranchChange}
        disabled={disabled}
      >
        <SelectTrigger id="branch-select">
          <SelectValue placeholder={TEXT.BRANCH_PLACEHOLDER} />
        </SelectTrigger>
        <SelectContent>
          {branches.map((branch) => (
            <SelectItem key={branch.name} value={branch.name}>
              {branch.name}
              {branch.name === defaultBranch && " (default)"}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
