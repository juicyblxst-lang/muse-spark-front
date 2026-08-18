import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DocumentStatus, MemoryKind, RelationshipType, TimelineEventKind } from "@/types/api";

const documentStatusLabels: Record<DocumentStatus, string> = {
  queued: "Queued",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
  needs_review: "Needs review",
};

const documentStatusTone: Record<DocumentStatus, string> = {
  queued: "bg-muted text-muted-foreground",
  processing: "bg-dormant/15 text-dormant",
  ready: "bg-signal/15 text-signal",
  failed: "bg-destructive/12 text-destructive",
  needs_review: "bg-ember/15 text-ember",
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <Badge variant="outline" className={cn("border-transparent", documentStatusTone[status])}>
      {documentStatusLabels[status]}
    </Badge>
  );
}

export function MemoryKindBadge({ kind }: { kind: MemoryKind }) {
  return (
    <Badge variant="outline" className="border-border bg-parchment text-foreground/80">
      {kind.replace("_", " ")}
    </Badge>
  );
}

export function RelationshipBadge({ type }: { type: RelationshipType }) {
  return (
    <Badge variant="outline" className="border-transparent bg-ember/12 text-ember">
      {type.replace(/_/g, " ")}
    </Badge>
  );
}

const eventTone: Record<TimelineEventKind, string> = {
  created: "bg-signal/15 text-signal",
  abandoned: "bg-destructive/12 text-destructive",
  revisited: "bg-ember/15 text-ember",
  milestone: "bg-dormant/15 text-dormant",
  mention: "bg-muted text-muted-foreground",
};

export function TimelineKindBadge({ kind }: { kind: TimelineEventKind }) {
  return (
    <Badge variant="outline" className={cn("border-transparent", eventTone[kind])}>
      {kind}
    </Badge>
  );
}
