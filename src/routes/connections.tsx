import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { AppShell } from "@/components/muse/AppShell";
import { LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { RelationshipBadge } from "@/components/muse/StatusBadge";
import { Button } from "@/components/ui/button";
import { museApi, queryKeys } from "@/lib/api";
import { formatDate, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/connections")({
  head: () => ({
    meta: [
      { title: "Connections — Muse" },
      {
        name: "description",
        content:
          "The people, projects, places and concepts in your archive, and how Muse sees them linked.",
      },
      { property: "og:title", content: "Connections — Muse" },
      {
        property: "og:description",
        content: "Entities and relationships across your creative memory.",
      },
    ],
  }),
  component: ConnectionsPage,
});

function ConnectionsPage() {
  const [entityId, setEntityId] = useState<string | undefined>(undefined);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.connections(entityId),
    queryFn: () => museApi.getConnections(entityId ? { entityId } : undefined),
  });

  const { data: all } = useQuery({
    queryKey: queryKeys.connections(undefined),
    queryFn: () => museApi.getConnections(),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Graph view"
        title="Connections"
        description="Muse links every entity it recognises. Pick one to see only what touches it."
        actions={
          entityId ? (
            <Button variant="outline" onClick={() => setEntityId(undefined)}>
              Clear filter
            </Button>
          ) : undefined
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {(all?.entities ?? []).map((entity) => (
          <button
            key={entity.id}
            type="button"
            onClick={() => setEntityId(entity.id)}
            className={cn(
              "rounded-full border border-border px-3 py-1 text-xs transition-colors",
              entityId === entity.id
                ? "border-transparent bg-ember text-ember-foreground"
                : "bg-card text-muted-foreground hover:bg-accent",
            )}
          >
            {entity.name}
          </button>
        ))}
      </div>

      {isLoading || !data ? (
        <LoadingState label="Tracing links" />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section>
            <h2 className="mb-4 text-2xl">Entities</h2>
            <ul className="space-y-3">
              {data.entities.map((entity) => (
                <li key={entity.id} className="surface-paper rounded-lg p-5">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-lg">{entity.name}</h3>
                    <span className="text-xs uppercase tracking-wide text-muted-foreground">
                      {entity.type}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{entity.description}</p>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {entity.mentionCount} mentions · {formatDate(entity.firstSeenAt)} →{" "}
                    {formatDate(entity.lastSeenAt)}
                  </p>
                  {entity.aliases.length > 0 ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      also: {entity.aliases.join(", ")}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="mb-4 text-2xl">Relationships</h2>
            <ul className="space-y-3">
              {data.relationships.map((relationship) => (
                <li key={relationship.id} className="surface-paper rounded-lg p-5">
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span>{relationship.from.name}</span>
                    <RelationshipBadge type={relationship.type} />
                    <span>{relationship.to.name}</span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{relationship.label}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span>confidence {formatPercent(relationship.confidence)}</span>
                    <span>{formatDate(relationship.observedAt)}</span>
                    {relationship.memoryIds.map((id) => (
                      <Link
                        key={id}
                        to="/memory/$memoryId"
                        params={{ memoryId: id }}
                        className="text-ember hover:underline"
                      >
                        {id}
                      </Link>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </AppShell>
  );
}
