import { Check, CircleDashed, Loader2, X } from "lucide-react";

import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ProcessingStageState } from "@/types/api";

const icons = {
  done: Check,
  active: Loader2,
  pending: CircleDashed,
  failed: X,
} as const;

export function ProcessingStages({ stages }: { stages: ProcessingStageState[] }) {
  return (
    <ol className="space-y-1">
      {stages.map((stage) => {
        const Icon = icons[stage.status];
        return (
          <li
            key={stage.stage}
            className={cn(
              "flex items-start gap-3 rounded-md px-3 py-3",
              stage.status === "active" && "bg-ember/8",
            )}
          >
            <Icon
              className={cn(
                "mt-0.5 size-4 shrink-0",
                stage.status === "done" && "text-signal",
                stage.status === "active" && "animate-spin text-ember",
                stage.status === "pending" && "text-muted-foreground",
                stage.status === "failed" && "text-destructive",
              )}
            />
            <div className="min-w-0">
              <p className="text-sm">{stage.label}</p>
              <p className="text-xs text-muted-foreground">
                {stage.detail ?? "Waiting"}
                {stage.completedAt ? ` · ${formatDateTime(stage.completedAt)}` : ""}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
