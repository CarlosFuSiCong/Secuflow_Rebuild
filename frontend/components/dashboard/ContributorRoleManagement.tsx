"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Search, Save, RefreshCw, AlertCircle, ChevronLeft, ChevronRight, Loader2, Download } from "lucide-react";
import {
  getProjectContributorsClassification,
  getFunctionalRoleChoices,
  updateContributorClassifications,
  analyzeTNMContributors,
  type ProjectContributor,
  type FunctionalRoleChoice,
  type ContributorUpdate,
} from "@/lib/api/contributors";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";

interface ContributorRoleManagementProps {
  projectId: string;
  hasRepository?: boolean;
}

export function ContributorRoleManagement({ projectId, hasRepository }: ContributorRoleManagementProps) {
  const [contributors, setContributors] = useState<ProjectContributor[]>([]);
  const [roleChoices, setRoleChoices] = useState<FunctionalRoleChoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState(""); // For debounced search
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [changes, setChanges] = useState<Map<string, ContributorUpdate>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const totalPages = Math.ceil(totalCount / pageSize);

  // Load role choices
  useEffect(() => {
    const loadRoleChoices = async () => {
      try {
        const choices = await getFunctionalRoleChoices();
        setRoleChoices(choices);
      } catch (err) {
        console.error("Failed to load role choices:", err);
      }
    };
    loadRoleChoices();
  }, []);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setCurrentPage(1); // Reset to first page on search
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [searchInput]);

  // Load contributors when filters or pagination changes
  useEffect(() => {
    loadContributors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, search, roleFilter, currentPage, pageSize]);

  const loadContributors = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getProjectContributorsClassification(projectId, {
        search: search || undefined,
        role: roleFilter !== "all" ? roleFilter : undefined,
        page: currentPage,
        page_size: pageSize,
      });
      setContributors(response.results);
      setTotalCount(response.count);
    } catch (err: unknown) {
      console.error("Failed to load contributors:", err);
      const axiosErr = err as { response?: { data?: { message?: string } } };
      setError(axiosErr?.response?.data?.message || "Failed to load contributors");
    } finally {
      setLoading(false);
    }
  };

  const handleImportContributors = async () => {
    setImporting(true);
    setError(null);
    try {
      toast.info("Importing contributors from TNM output...");
      await analyzeTNMContributors(projectId);
      toast.success("Contributors imported successfully.");
      await loadContributors();
    } catch (err: any) {
      const msg =
        err?.response?.data?.errorMessage ||
        err?.response?.data?.message ||
        err?.message ||
        "Failed to import contributors";
      toast.error(msg);
      setError(msg);
    } finally {
      setImporting(false);
    }
  };

  const handleRoleChange = (contributorId: string, role: string) => {
    const updated = new Map(changes);
    const existing = updated.get(contributorId) || { id: contributorId };
    updated.set(contributorId, { ...existing, functional_role: role });
    setChanges(updated);

    // Update local state
    setContributors(
      contributors.map((c) =>
        c.id === contributorId ? { ...c, functional_role: role } : c
      )
    );
  };

  const handleCoreChange = (contributorId: string, isCore: boolean) => {
    const updated = new Map(changes);
    const existing = updated.get(contributorId) || { id: contributorId };
    updated.set(contributorId, { ...existing, is_core_contributor: isCore });
    setChanges(updated);

    // Update local state
    setContributors(
      contributors.map((c) =>
        c.id === contributorId ? { ...c, is_core_contributor: isCore } : c
      )
    );
  };

  const handleSave = async () => {
    if (changes.size === 0) return;

    setSaving(true);
    setError(null);

    try {
      const updates = Array.from(changes.values());
      const result = await updateContributorClassifications(projectId, updates);
      toast.success(`Successfully updated ${result.updated_count} contributors`);
      setChanges(new Map());
    } catch (err: unknown) {
      console.error("Failed to save changes:", err);
      const axiosErr = err as { response?: { data?: { message?: string } } };
      const msg = axiosErr?.response?.data?.message || "Failed to save changes";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const _getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case "developer":
        return "default";
      case "security":
        return "destructive";
      case "ops":
        return "outline";
      default:
        return "secondary";
    }
  };

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-xs">Loading contributors...</span>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-0.5">
            Contributor Roles
          </p>
          <p className="text-sm text-muted-foreground">
            Set functional roles for MC-STC analysis ({totalCount} total)
          </p>
        </div>
        <div className="flex items-center gap-2">
          {changes.size > 0 && (
            <span className="text-sm text-muted-foreground">
              {changes.size} unsaved changes
            </span>
          )}
          <Button
            onClick={handleSave}
            disabled={saving || changes.size === 0}
            size="sm"
          >
            {saving ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Save Changes
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by login or email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={roleFilter} onValueChange={(value) => {
          setRoleFilter(value);
          setCurrentPage(1);
        }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {roleChoices.map((choice) => (
              <SelectItem key={choice.value} value={choice.value}>
                {choice.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={pageSize.toString()} onValueChange={(value) => {
          setPageSize(parseInt(value));
          setCurrentPage(1);
        }}>
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10 / page</SelectItem>
            <SelectItem value="25">25 / page</SelectItem>
            <SelectItem value="50">50 / page</SelectItem>
            <SelectItem value="100">100 / page</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="ghost" size="icon" onClick={loadContributors}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Load error */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Contributors table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b">
              <tr className="text-xs font-medium tracking-widest uppercase text-muted-foreground">
                <th className="text-left p-3">Contributor</th>
                <th className="text-left p-3">Activity</th>
                <th className="text-left p-3">Role</th>
                <th className="text-left p-3">Core</th>
              </tr>
            </thead>
            <tbody>
              {contributors.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-8 text-center">
                    {totalCount === 0 ? (
                      <div className="flex flex-col items-center gap-3 text-muted-foreground">
                        <span className="text-sm">No contributors found. TNM analysis may not be complete yet.</span>
                        {hasRepository && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleImportContributors}
                            disabled={importing}
                          >
                            {importing ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />
                            ) : (
                              <Download className="h-3.5 w-3.5 mr-2" />
                            )}
                            Import from TNM
                          </Button>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-muted-foreground">No contributors match the current filters.</span>
                    )}
                  </td>
                </tr>
              ) : (
                contributors.map((contributor) => (
                  <tr key={contributor.id} className="border-b hover:bg-muted/50">
                    <td className="p-3">
                      <div className="flex flex-col">
                        <span className="font-medium">{contributor.contributor_login}</span>
                        <span className="text-xs text-muted-foreground">
                          {contributor.contributor_email}
                        </span>
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-col text-sm">
                        <span>{contributor.commits_count} commits</span>
                        <span className="text-xs text-muted-foreground">
                          {contributor.total_modifications} modifications
                        </span>
                      </div>
                    </td>
                    <td className="p-3">
                      <Select
                        value={contributor.functional_role}
                        onValueChange={(value) => handleRoleChange(contributor.id, value)}
                      >
                        <SelectTrigger className="w-[150px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {roleChoices.map((choice) => (
                            <SelectItem key={choice.value} value={choice.value}>
                              {choice.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="p-3">
                      <Checkbox
                        checked={contributor.is_core_contributor}
                        onCheckedChange={(checked) =>
                          handleCoreChange(contributor.id, checked === true)
                        }
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} contributors
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(pageNum)}
                      className="w-8 h-8 p-0"
                    >
                      {pageNum}
                    </Button>
                  );
                })}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Info */}
      <div className="text-xs text-muted-foreground border border-border rounded px-3 py-2">
        Assign functional roles to contributors before running MC-STC analysis for role-specific coordination insights.
      </div>
    </div>
  );
}
