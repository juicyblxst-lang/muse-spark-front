import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { Button } from "@/components/ui/button";
import { museApi, queryKeys } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/revivals/")({
  head: () => ({
    meta: [
      { title: "Revivals — Muse" },
      {
        name: "description",
        content:
          "Every time Muse brought an abandoned idea back, with the reasoning and the sources behind it.",
      },
      { property: "og:title", content: "Revivals — Muse" },
      {
        property: "og:description",
        content: "Revived ideas from your own archive, each traced to its material.",
      },
    ],
  }),
  component: RevivalsPage,
});

function RevivalsPage() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.revivals,
    queryFn: () => museApi.listRevivals(),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Step six"
        title="Revivals"
        description="Where Muse took dormant material and proposed a way back into it."
      />

      {isLoading ? (
        <LoadingState label="Gathering revivals" />
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No revivals yet"
          description="Open a memory and ask Muse for next steps."
          action={
            <Button asChild>
              <Link to="/memory">Search memory</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {data.map((revival) => (
            <Link
              key={revival.id}
              to="/revivals/$revivalId"
              params={{ revivalId: revival.id }}
              className="surface-paper block rounded-lg p-5 hover:shadow-lift"
            >
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <span className="uppercase tracking-[0.14em]">
                  {revival.intent.replace("_", " ")}
                </span>
                <span>{formatDateTime(revival.createdAt)}</span>
                <span>{revival.suggestions.length} suggestion(s)</span>
              </div>
              <h2 className="mt-3 text-xl">{revival.memoryTitle}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{revival.summary}</p>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}
