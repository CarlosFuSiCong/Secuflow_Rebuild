import Card from "@/components/horizon/Card";
import type { ProjectHeaderProps } from "@/lib/types";
import { DeleteProjectButton } from "./DeleteProjectButton";

export function ProjectHeader({ project }: ProjectHeaderProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              {project.name}
            </h2>
            <p className="text-muted-foreground mt-1">
              {project.description}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {project.repo_url}
            </p>
          </div>
          <DeleteProjectButton projectId={project.id} projectName={project.name} />
        </div>
      </div>
    </Card>
  );
}