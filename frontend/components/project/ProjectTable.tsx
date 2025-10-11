"use client";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
} from "@/components/ui/table";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { ProjectTableRow } from "./ProjectTableRow";
import type { Project } from "@/lib/api/projects";
import type { EnhancedProject } from "@/lib/utils/project-helpers";

const TEXT = {
  HEADER_PROJECT: "Project",
  HEADER_STC_RISK: "STC Risk",
  HEADER_MCSTC_RISK: "MCSTC Risk",
  HEADER_MEMBERS: "Members",
  HEADER_LAST_ANALYSIS: "Last Analysis",
  HEADER_CREATED: "Created",
  PAGINATION_PREVIOUS: "Previous",
  PAGINATION_NEXT: "Next",
};

interface ProjectTableProps {
  projects: (Project | EnhancedProject)[];
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export function ProjectTable({
  projects,
  currentPage = 1,
  totalPages = 1,
  onPageChange,
}: ProjectTableProps) {

  const renderPaginationItems = () => {
    const items = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        items.push(
          <PaginationItem key={i}>
            <PaginationLink
              href="#"
              size="icon"
              isActive={i === currentPage}
              onClick={(e) => {
                e.preventDefault();
                onPageChange?.(i);
              }}
            >
              {i}
            </PaginationLink>
          </PaginationItem>
        );
      }
    } else {
      // Show first, last, and pages around current
      items.push(
        <PaginationItem key={1}>
          <PaginationLink
            href="#"
            size="icon"
            isActive={1 === currentPage}
            onClick={(e) => {
              e.preventDefault();
              onPageChange?.(1);
            }}
          >
            1
          </PaginationLink>
        </PaginationItem>
      );

      if (currentPage > 3) {
        items.push(
          <PaginationItem key="ellipsis-start">
            <PaginationEllipsis />
          </PaginationItem>
        );
      }

      for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
        items.push(
          <PaginationItem key={i}>
            <PaginationLink
              href="#"
              size="icon"
              isActive={i === currentPage}
              onClick={(e) => {
                e.preventDefault();
                onPageChange?.(i);
              }}
            >
              {i}
            </PaginationLink>
          </PaginationItem>
        );
      }

      if (currentPage < totalPages - 2) {
        items.push(
          <PaginationItem key="ellipsis-end">
            <PaginationEllipsis />
          </PaginationItem>
        );
      }

      items.push(
        <PaginationItem key={totalPages}>
          <PaginationLink
            href="#"
            size="icon"
            isActive={totalPages === currentPage}
            onClick={(e) => {
              e.preventDefault();
              onPageChange?.(totalPages);
            }}
          >
            {totalPages}
          </PaginationLink>
        </PaginationItem>
      );
    }

    return items;
  };

  return (
    <div className="overflow-hidden rounded-md border">
      <div className="overflow-x-auto">
        <Table className="min-w-[640px]">
          <TableHeader className="h-12">
            <TableRow>
              <TableHead className="text-foreground font-semibold">{TEXT.HEADER_PROJECT}</TableHead>
              <TableHead className="text-foreground font-semibold hidden lg:table-cell">
                {TEXT.HEADER_STC_RISK}
              </TableHead>
              <TableHead className="text-foreground font-semibold hidden lg:table-cell">
                {TEXT.HEADER_MCSTC_RISK}
              </TableHead>
              <TableHead className="text-foreground font-semibold hidden md:table-cell">
                {TEXT.HEADER_MEMBERS}
              </TableHead>
              <TableHead className="text-foreground font-semibold hidden xl:table-cell">
                {TEXT.HEADER_LAST_ANALYSIS}
              </TableHead>
              <TableHead className="text-foreground font-semibold">{TEXT.HEADER_CREATED}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {projects.map((project) => (
              <ProjectTableRow
                key={project.id}
                project={project}
              />
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-muted flex items-center justify-end border-t p-4">
          <Pagination className="hidden justify-end md:flex">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    if (currentPage > 1) onPageChange?.(currentPage - 1);
                  }} size={undefined} />
              </PaginationItem>
              {renderPaginationItems()}
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    if (currentPage < totalPages) onPageChange?.(currentPage + 1);
                  }} size={undefined} />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
          <div className="flex items-center justify-end space-x-2 md:hidden">
            <Button
              variant="outline"
              onClick={() => currentPage > 1 && onPageChange?.(currentPage - 1)}
              disabled={currentPage === 1}
            >
              {TEXT.PAGINATION_PREVIOUS}
            </Button>
            <Button
              variant="outline"
              onClick={() => currentPage < totalPages && onPageChange?.(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              {TEXT.PAGINATION_NEXT}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
