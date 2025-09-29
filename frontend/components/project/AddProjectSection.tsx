import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function AddProjectSection() {
  return (
    <section className="flex flex-col gap-4 lg:gap-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Add New Project</h2>
        <p className="text-sm text-muted-foreground lg:text-base">
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
          <p className="text-xs text-muted-foreground">
            Enter the full GitHub repository URL (e.g., https://github.com/username/repository)
          </p>
        </CardContent>
      </Card>
    </section>
  );
}