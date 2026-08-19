import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/muse/AppShell";
import { LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { TimelineKindBadge } from "@/components/muse/StatusBadge";
import { museApi, queryKeys } from "@/lib/api";
import { formatDate, formatYear } from "@/lib/format";

export const Route = createFileRoute("/timeline")({
  head: () => ({
    meta: [
      { title: "Timeline — Muse" },
      {
        name: "description",
        content: "Your creative history in order, including the gaps where a project went quiet.",
      },
      { property: "og:title", content: "Timeline — Muse" },
      { property: "og:description", content: "When each idea was made, revisited or abandoned." },
    ],
  }),
  component: TimelinePage,
});

function TimelinePage() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.timeline,
    queryFn: () => museApi.getTimeline(),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Temporal view"
        title="Timeline"
        description="Muse places every memory in time so you can see when work started, stalled and came back."
      />

      {isLoading || !data ? (
        <LoadingState label="Ordering your history" />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <ol className="relative space-y-4 border-l border-border pl-6">
            {data.events.map((event) => (
              <li key={event.id} className="relative">
                <span className="absolute -left-[29px] top-4 size-2.5 rounded-full bg-ember" />
                <div className="surface-paper rounded-lg p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <TimelineKindBadge kind={event.kind} />
                    <span className="text-xs text-muted-foreground">
                      {formatDate(event.occurredAt)}
                    </span>
                  </div>
                  <h3 className="mt-3 text-xl">{event.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{event.description}</p>
                  <div className="mt-3 flex flex-wrap gap-3 text-xs">
                    {event.memoryIds.map((id) => (
                      <Link
                        key={id}
                        to="/memory/$memoryId"
                        params={{ memoryId: id }}
                        className="text-ember hover:underline"
                      >
                        memory {id}
                      </Link>
                    ))}
                    {event.entities.map((entity) => (
                      <span key={entity.id} className="rounded bg-parchment px-1.5 py-0.5">
                        {entity.name}
                      </span>
                    ))}
                  </div>
                </div>
              </li>
            ))}
          </ol>

          <aside className="space-y-4">
            <div className="surface-paper rounded-lg p-5 text-sm">
              <h2 className="text-xl">Span</h2>
              <p className="mt-2 text-muted-foreground">
                {formatYear(data.earliest)} — {formatYear(data.latest)}
              </p>
            </div>
            <div className="surface-paper rounded-lg p-5">
              <h2 className="text-xl">Quiet stretches</h2>
              <ul className="mt-3 space-y-3 text-sm text-muted-foreground">
                {data.gaps.map((gap) => (
                  <li key={`${gap.from}-${gap.to}`} className="border-l-2 border-dormant/50 pl-3">
                    {gap.days} days
                    <br />
                    {formatDate(gap.from)} → {formatDate(gap.to)}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      )}
    </AppShell>
  );
}
