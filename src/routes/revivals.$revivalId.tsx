import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { SourceList } from "@/components/muse/SourceList";
import { Button } from "@/components/ui/button";
import { museApi, queryKeys } from "@/lib/api";
import { formatDateTime, formatPercent } from "@/lib/format";

export const Route = createFileRoute("/revivals/$revivalId")({
  head: () => ({
    meta: [
      { title: "Revival result — Muse" },
      {
        name: "description",
        content:
          "What Muse proposes for a revived idea: routes forward, next steps and the passages that support them.",
      },
      { property: "og:title", content: "Revival result — Muse" },
      {
        property: "og:description",
        content: "A revived idea with cited next steps from your own archive.",
      },
    ],
  }),
  component: RevivalDetailPage,
});

function RevivalDetailPage() {
  const { revivalId } = Route.useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.revival(revivalId),
    queryFn: () => museApi.getRevival(revivalId),
  });

  if (isLoading) {
    return (
      <AppShell>
        <LoadingState label="Assembling the revival" />
      </AppShell>
    );
  }

  if (isError || !data) {
    return (
      <AppShell>
        <EmptyState
          title="Revival not found"
          action={
            <Button asChild>
              <Link to="/revivals">All revivals</Link>
            </Button>
          }
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow={`${data.intent.replace("_", " ")} · ${formatDateTime(data.createdAt)}`}
        title={data.memoryTitle}
        description={data.summary}
        actions={
          <Button variant="outline" asChild>
            <Link to="/memory/$memoryId" params={{ memoryId: data.memoryId }}>
              Open memory
            </Link>
          </Button>
        }
      />

      <section className="space-y-4">
        {data.suggestions.map((suggestion) => (
          <article key={suggestion.id} className="surface-paper rounded-lg p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-2xl">{suggestion.title}</h2>
              <span className="text-xs text-muted-foreground">
                confidence {formatPercent(suggestion.confidence)}
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              {suggestion.rationale}
            </p>
            <ul className="mt-5 space-y-2">
              {suggestion.nextSteps.map((step) => (
                <li key={step} className="flex items-start gap-2 text-sm">
                  <ArrowRight className="mt-0.5 size-4 shrink-0 text-ember" />
                  {step}
                </li>
              ))}
            </ul>
            <div className="mt-5 flex flex-wrap gap-3 text-xs">
              {suggestion.supportingMemoryIds.map((id) => (
                <Link
                  key={id}
                  to="/memory/$memoryId"
                  params={{ memoryId: id }}
                  className="text-ember hover:underline"
                >
                  supported by {id}
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="mt-10">
        <h2 className="mb-4 text-2xl">Sources cited</h2>
        <SourceList sources={data.sources} />
      </section>
    </AppShell>
  );
}
