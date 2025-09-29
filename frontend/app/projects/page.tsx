"use client";

import { Separator } from "@/components/ui/separator";
import { Navbar } from "@/components/project/Navbar";
import { AddProjectSection } from "@/components/project/AddProjectSection";
import { ProjectsList } from "@/components/project/ProjectsList";

// ===========================================
// Main Projects Page Component
// ===========================================
export default function ProjectsPage() {
  return (
    <div className="bg-background">
      {/* Navigation Bar */}
      <Navbar />

      {/* Main Content Area */}
      <main>
        <div className="container mx-auto flex flex-col gap-6 p-4 lg:gap-8 lg:p-6">
          {/* Add New Project Section */}
          <AddProjectSection />

          {/* Section Divider */}
          <Separator />

          {/* Projects List Section */}
          <ProjectsList />
        </div>
      </main>
    </div>
  );
}
