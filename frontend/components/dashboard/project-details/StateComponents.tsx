import Card from "@/components/horizon/Card";
import type { EmptyStateProps, LoadingStateProps, ErrorStateProps } from "@/lib/types";

export function EmptyState({ message }: EmptyStateProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-muted-foreground">{message}</p>
        </div>
      </div>
    </Card>
  );
}

export function LoadingState({ message = "Loading project details..." }: LoadingStateProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
          <p className="text-muted-foreground">{message}</p>
        </div>
      </div>
    </Card>
  );
}

export function ErrorState({ error }: ErrorStateProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-destructive">{error}</p>
        </div>
      </div>
    </Card>
  );
}
