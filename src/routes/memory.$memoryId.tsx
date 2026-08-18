import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { SourceList } from "@/components/muse/SourceList";
import { MemoryKindBadge, RelationshipBadge } from "@/components/muse/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { museApi, queryKeys } from "@/lib/api";
import { formatDate, formatPercent, formatRelative } from "@/lib/format";
import type { RevivalRequest } from "@/types/api";

export const Route = createFileRoute("/memory/$memoryId")({
  head: () => ({
    meta: [
      { title: "Memory — Muse" },
      {
        name: "description",
        content:
          "A single remembered idea with its entities, relationships, dates and source passages.",
      },
      { property: "og:title", content: "Memory — Muse" },
      {
        property: "og:description",
        content: "One remembered idea, fully traceable back to the material it came from.",
      },
    ],
  }),
  component: MemoryDetailPage,
});

const intents: Array<{ value: RevivalRequest["intent"]; label: string }> = [
  { value: "next_steps", label: "Give me next steps" },
  { value: "expand", label: "Expand this idea" },
  { value: "reframe", label: "Reframe it" },
  { value: "combine", label: "Combine with related work" },
];

function MemoryDetailPage() {
  const { memoryId } = Route.useParams();
  const navigate = useNavigate();
  const [intent, setIntent] = useState<RevivalRequest["intent"]>("next_steps");
  const [note, setNote] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.memory(memoryId),
    queryFn: () => museApi.getMemory(memoryId),
  });

  const revive = useMutation({
    mutationFn: () => museApi.requestRevival({ memoryId, intent, note: note || undefined }),
    onSuccess: async (result) => {
      toast.success("Muse revived this idea");
      await navigate({ to: "/revivals/$revivalId", params: { revivalId: result.id } });
    },
  });

  if (isLoading) {
    return (
      <AppShell>
        <LoadingState label="Recalling" />
      </AppShell>
    );
  }

  if (isError || !data) {
    return (
      <AppShell>
        <EmptyState
          title="Memory not found"
          action={
            <Button asChild>
              <Link to="/memory">Back to search</Link>
            </Button>
          }
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow={`From ${data.documentTitle}`}
        title={data.title}
        description={`Written ${formatDate(data.occurredAt)} · ${formatRelative(
          data.occurredAt,
        )} · confidence ${formatPercent(data.confidence)} · dormancy ${formatPercent(data.dormancy)}`}
        actions={<MemoryKindBadge kind={data.kind} />}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-8">
          <section className="surface-paper rounded-lg p-6">
            <p className="whitespace-pre-line text-base leading-relaxed">{data.body}</p>
          </section>

          <section>
            <h2 className="mb-4 text-2xl">Where this came from</h2>
            <SourceList sources={data.sources} />
          </section>

          <section>
            <h2 className="mb-4 text-2xl">Relationships</h2>
            {data.relationships.length === 0 ? (
              <p className="text-sm text-muted-foreground">No relationships recorded yet.</p>
            ) : (
              <ul className="space-y-2">
                {data.relationships.map((relationship) => (
                  <li
                    key={relationship.id}
                    className="surface-paper flex flex-wrap items-center gap-3 rounded-lg px-4 py-3 text-sm"
                  >
                    <span>{relationship.from.name}</span>
                    <RelationshipBadge type={relationship.type} />
                    <span>{relationship.to.name}</span>
                    <span className="text-xs text-muted-foreground">{relationship.label}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="surface-paper bg-ember-wash rounded-lg p-6">
            <h2 className="text-2xl">Revive this idea</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Muse works from your own material only — every suggestion cites the passages behind
              it.
            </p>
            <div className="mt-5 space-y-3">
              <Select
                value={intent}
                onValueChange={(value) => setIntent(value as RevivalRequest["intent"])}
              >
                <SelectTrigger className="w-full sm:w-72">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {intents.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="Optional: what are you working on right now?"
                rows={3}
              />
              <Button onClick={() => revive.mutate()} disabled={revive.isPending}>
                <Sparkles className="mr-1 size-4" />
                {revive.isPending ? "Reviving…" : "Ask Muse"}
              </Button>
            </div>
          </section>
        </div>

        <aside className="space-y-4">
          <div className="surface-paper rounded-lg p-5">
            <h2 className="text-xl">Entities</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {data.entities.map((entity) => (
                <li key={entity.id} className="flex items-center justify-between gap-2">
                  <span>{entity.name}</span>
                  <span className="text-xs text-muted-foreground">{entity.type}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="surface-paper rounded-lg p-5">
            <h2 className="text-xl">Related memories</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {data.relatedMemoryIds.map((id) => (
                <li key={id}>
                  <Link
                    to="/memory/$memoryId"
                    params={{ memoryId: id }}
                    className="text-ember hover:underline"
                  >
                    {id}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <Button variant="outline" className="w-full" asChild>
            <Link to="/corrections">Correct this memory</Link>
          </Button>
        </aside>
      </div>
    </AppShell>
  );
}
