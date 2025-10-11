import Card from "@/components/horizon/Card";
import type { ProjectHeaderProps } from "@/lib/types";

export function ProjectHeader({ project }: ProjectHeaderProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="mb-4">
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
      </div>
    </Card>
  );
}