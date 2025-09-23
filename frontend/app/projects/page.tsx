"use client";

import { Logo } from "@/components/ui/logo";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Menu, Zap, Search, X, Download, ExternalLink } from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import Link from "next/link";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";

import { useState } from "react";

function Navbar1() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  const MobileTopBar = () => (
    <div
      className={`bg-background flex h-14 items-center justify-between px-4 ${!isMenuOpen ? "border-border border-b" : ""
        }`}
    >
      <Button
        variant="ghost"
        onClick={toggleMenu}
        className="relative -ml-2 flex h-9 w-9 items-center justify-center [&_svg]:size-5"
      >
        <span
          className={`absolute transition-all duration-300 ${isMenuOpen ? "rotate-90 opacity-0" : "rotate-0 opacity-100"
            }`}
        >
          <Menu />
        </span>
        <span
          className={`absolute transition-all duration-300 ${isMenuOpen ? "rotate-0 opacity-100" : "-rotate-90 opacity-0"
            }`}
        >
          <X />
        </span>
      </Button>

      <Logo className="absolute left-1/2 h-8 w-8 -translate-x-1/2 transform" />

      <div className="absolute right-4 flex items-center gap-3">
        <Button variant="ghost" className="h-9 w-9 p-0 [&_svg]:size-5">
          <Search className="text-muted-foreground" />
        </Button>
        <Button className="h-9 w-9 p-0 [&_svg]:size-5">
          <Zap />
        </Button>
      </div>
    </div>
  );

  const NavItems = ({ isMobile = false }) => {
    const linkClasses = `font-medium ${isMobile ? "text-base" : "text-sm"} ${isMobile
      ? "text-muted-foreground"
      : "text-muted-foreground hover:bg-primary/5"
      } px-3 py-2 rounded-md`;

    return (
      <>
        <Link href="#" className={`${linkClasses} text-primary`}>
          Projects
        </Link>
        <Link href="#" className={linkClasses}>
          Dashboard
        </Link>
        <Link href="#" className={linkClasses}>
          Analytics
        </Link>
        <Link href="#" className={linkClasses}>
          Settings
        </Link>
      </>
    );
  };

  return (
    <>
      <nav className="border-border bg-background hidden h-16 border-b shadow-sm lg:block">
        <div className="container mx-auto flex h-full items-center justify-between px-6">
          <div className="flex items-center gap-x-4">
            <Logo />
            <div className="flex items-center gap-x-1">
              <NavItems />
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="icon">
              <Search className="text-muted-foreground h-5 w-5" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Avatar className="cursor-pointer">
                  <AvatarImage
                    src="https://github.com/shadcn.png"
                    alt="@shadcn"
                  />
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>My Profile</DropdownMenuItem>
                <DropdownMenuItem>Account</DropdownMenuItem>
                <DropdownMenuItem>Billing</DropdownMenuItem>
                <Separator className="my-1" />
                <DropdownMenuItem>Sign Out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button>
              <Zap className="h-4 w-4" /> Upgrade
            </Button>
          </div>
        </div>
      </nav>

      <nav className="lg:hidden">
        <MobileTopBar />
      </nav>

      {isMenuOpen && (
        <div className="border-border bg-background border-b lg:hidden">
          <div className="flex flex-col">
            <div className="flex-grow overflow-y-auto p-2">
              <div className="flex flex-col">
                <NavItems isMobile={true} />
              </div>
            </div>
            <Separator />
            <div className="p-2">
              <div className="flex items-center space-x-3 p-2">
                <Avatar>
                  <AvatarImage
                    src="https://github.com/shadcn.png"
                    alt="@shadcn"
                  />
                  <AvatarFallback>JD</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">John Doe</p>
                  <p className="text-muted-foreground text-sm">
                    hi@shadcndesign.com
                  </p>
                </div>
              </div>
              <div>
                <Link
                  href="#"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  My profile
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  Account settings
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  Billing
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  Sign out
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Page Header

function PageHeader3() {
  return (
    <div className="border-border bg-background border-b pt-0 pb-4 md:pb-6">
      <nav className="border-border mb-6 border-b">
        <div className="container mx-auto flex overflow-x-auto px-2 lg:px-3.5">
          <Link
            href="#"
            className="text-foreground flex-shrink-0 py-1.5 text-sm"
          >
            <span className="hover:bg-muted block rounded-md px-2.5 py-2">
              Profile
            </span>
          </Link>
          <Link
            href="#"
            className="text-muted-foreground flex-shrink-0 py-1.5 text-sm"
          >
            <span className="hover:bg-muted block rounded-md px-2.5 py-2">
              Account
            </span>
          </Link>
          <Link
            href="#"
            className="text-muted-foreground flex-shrink-0 py-1.5 text-sm"
          >
            <span className="hover:bg-muted block rounded-md px-2.5 py-2">
              Analytics
            </span>
          </Link>
          <Link
            href="#"
            className="border-primary text-foreground flex-shrink-0 border-b-2 py-1.5 text-sm"
          >
            <span className="hover:bg-muted block rounded-md px-2.5 py-2">
              Projects
            </span>
          </Link>
          <Link
            href="#"
            className="text-muted-foreground flex-shrink-0 py-1.5 text-sm"
          >
            <span className="hover:bg-muted block rounded-md px-2.5 py-2">
              Members
            </span>
          </Link>
        </div>
      </nav>
      <div className="container mx-auto flex flex-col gap-6 px-4 lg:px-6">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
              Projects
            </h1>
            <p className="text-muted-foreground text-sm lg:text-base">
              Manage your projects and add new repositories from GitHub.
            </p>
          </div>

          <div>
            <Button variant="outline">Contact support</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  return (
    <div className="bg-background">
      <Navbar1 />
      <PageHeader3 />
      <main>
        <div className="container mx-auto flex flex-col gap-6 p-4 lg:gap-8 lg:p-6">
          <section className="flex flex-col gap-4 lg:gap-6">
            <div className="space-y-1">
              <h2 className="text-xl font-semibold">Add New Project</h2>
              <p className="text-muted-foreground text-sm lg:text-base">
                Import a project from GitHub by providing the repository URL.
              </p>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Import from GitHub</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col gap-2 md:flex-row md:gap-4">
                  <div className="flex-1">
                    <Input
                      placeholder="https://github.com/username/repository"
                      className="w-full"
                    />
                  </div>
                  <Button className="md:w-auto">
                    Import Project
                  </Button>
                </div>
                <p className="text-muted-foreground text-xs">
                  Enter the full GitHub repository URL (e.g., https://github.com/username/repository)
                </p>
              </CardContent>
            </Card>
          </section>
          <Separator />
          {/* Invoices */}
          <section className="flex flex-col gap-4 lg:gap-6">
            <div className="space-y-1">
              <h2 className="text-xl font-semibold">Your Projects</h2>
              <p className="text-muted-foreground text-sm lg:text-base">
                View and manage all your imported GitHub projects.
              </p>
            </div>
            <div className="flex flex-col justify-between gap-2 md:flex-row">
              <div className="relative order-last md:order-first md:mb-0 md:w-64">
                <Search
                  className="text-muted-foreground absolute top-1/2 left-3 -translate-y-1/2 transform"
                  size={18}
                />
                <Input className="pl-10" placeholder="Search" />
              </div>
              <Button>
                Export Project
              </Button>
            </div>
            <div className="overflow-hidden rounded-md border">
              <div className="overflow-x-auto">
                <Table className="min-w-[640px]">
                  <TableHeader className="h-12">
                    <TableRow>
                      <TableHead className="text-foreground w-10 pt-1">
                        <Checkbox />
                      </TableHead>
                      <TableHead className="text-foreground">Project Name</TableHead>
                      <TableHead className="text-foreground hidden md:table-cell">
                        Last Updated
                      </TableHead>
                      <TableHead className="text-foreground">Status</TableHead>
                      <TableHead className="text-foreground">Repository</TableHead>
                      <TableHead className="text-foreground w-[40px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {[
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
                    ].map((project) => (
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
                        <TableCell className="text-muted-foreground text-sm">
                          {project.repository}
                        </TableCell>
                        <TableCell>...</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="bg-muted flex items-center justify-end border-t p-4">
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
                <div className="flex items-center justify-end space-x-2 md:hidden">
                  <Button variant="outline">Previous</Button>
                  <Button variant="outline">Next</Button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
