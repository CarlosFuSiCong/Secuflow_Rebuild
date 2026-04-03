import Card from "@/components/horizon/Card";
import { Loader2 } from "lucide-react";
import type { EmptyStateProps, LoadingStateProps, ErrorStateProps } from "@/lib/types";

export function EmptyState({ message }: EmptyStateProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
    </Card>
  );
}

export function LoadingState({ message = "Loading project details..." }: LoadingStateProps) {
  return (
    <Card>
      <div className="p-6">
        <div className="flex flex-col items-center py-12 gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <p className="text-xs">{message}</p>
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
          <p className="text-sm text-destructive">{error}</p>
        </div>
      </div>
    </Card>
  );
}
