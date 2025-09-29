import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Search } from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";

export function ProjectsList() {
  const projects = [
    {
      id: 1,
      name: "secuflow-rebuild",
      lastUpdated: "2 hours ago",
      status: "Active",
      repository: "github.com/user/secuflow-rebuild",
    },
    {
      id: 2,
      name: "web-scanner",
      lastUpdated: "1 day ago",
      status: "Active",
      repository: "github.com/user/web-scanner",
    },
    {
      id: 3,
      name: "api-security-tool",
      lastUpdated: "3 days ago",
      status: "Inactive",
      repository: "github.com/user/api-security-tool",
    },
    {
      id: 4,
      name: "vulnerability-db",
      lastUpdated: "1 week ago",
      status: "Active",
      repository: "github.com/user/vulnerability-db",
    },
    {
      id: 5,
      name: "security-dashboard",
      lastUpdated: "2 weeks ago",
      status: "Inactive",
      repository: "github.com/user/security-dashboard",
    },
  ];

  return (
    <section className="flex flex-col gap-4 lg:gap-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Your Projects</h2>
        <p className="text-sm text-muted-foreground lg:text-base">
          View and manage all your imported GitHub projects.
        </p>
      </div>

      {/* Search and Export Controls */}
      <div className="flex flex-col justify-between gap-2 md:flex-row">
        <div className="relative order-last md:order-first md:mb-0 md:w-64">
          <Search
            className="absolute top-1/2 left-3 -translate-y-1/2 transform text-muted-foreground"
            size={18}
          />
          <Input className="pl-10" placeholder="Search" />
        </div>
        <Button>
          Export Project
        </Button>
      </div>

      {/* Projects Data Table */}
      <div className="overflow-hidden rounded-md border">
        <div className="overflow-x-auto">
          <Table className="min-w-[640px]">
            <TableHeader className="h-12">
              <TableRow>
                <TableHead className="w-10 pt-1 text-foreground">
                  <Checkbox />
                </TableHead>
                <TableHead className="text-foreground">Project Name</TableHead>
                <TableHead className="hidden text-foreground md:table-cell">
                  Last Updated
                </TableHead>
                <TableHead className="text-foreground">Status</TableHead>
                <TableHead className="text-foreground">Repository</TableHead>
                <TableHead className="w-[40px] text-foreground"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {projects.map((project) => (
                <TableRow key={project.id}>
                  <TableCell className="pt-5">
                    <Checkbox />
                  </TableCell>
                  <TableCell className="font-medium">
                    {project.name}
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    {project.lastUpdated}
                  </TableCell>
                  <TableCell>
                    <Badge variant={project.status === "Active" ? "default" : "secondary"}>
                      {project.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {project.repository}
                  </TableCell>
                  <TableCell>...</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center justify-end border-t bg-muted p-4">
          <Pagination className="hidden justify-end md:flex">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious href="#" />
              </PaginationItem>
              <PaginationItem>
                <PaginationLink href="#">1</PaginationLink>
              </PaginationItem>
              <PaginationItem>
                <PaginationLink href="#" isActive>
                  2
                </PaginationLink>
              </PaginationItem>
              <PaginationItem>
                <PaginationLink href="#">3</PaginationLink>
              </PaginationItem>
              <PaginationItem>
                <PaginationEllipsis />
              </PaginationItem>
              <PaginationItem>
                <PaginationNext href="#" />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
          {/* Mobile Pagination */}
          <div className="flex items-center justify-end space-x-2 md:hidden">
            <Button variant="outline">Previous</Button>
            <Button variant="outline">Next</Button>
          </div>
        </div>
      </div>
    </section>
  );
}