"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

const TEXT = {
  SEARCH_PLACEHOLDER: "Search",
  EXPORT_BUTTON: "Export Project",
};

interface ProjectSearchBarProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onExport?: () => void;
}

export function ProjectSearchBar({
  searchQuery,
  onSearchChange,
  onExport,
}: ProjectSearchBarProps) {
  return (
    <div className="flex flex-col justify-between gap-2 md:flex-row">
      <div className="relative order-last md:order-first md:mb-0 md:w-64">
        <Search
          className="text-muted-foreground absolute top-1/2 left-3 -translate-y-1/2 transform"
          size={18}
        />
        <Input
          className="pl-10"
          placeholder={TEXT.SEARCH_PLACEHOLDER}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <Button onClick={onExport}>
        {TEXT.EXPORT_BUTTON}
      </Button>
    </div>
  );
}
