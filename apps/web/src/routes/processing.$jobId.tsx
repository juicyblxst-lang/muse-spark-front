import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { ProcessingStages } from "@/components/muse/ProcessingStages";
import { StatCard } from "@/components/muse/StatCard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { museApi, queryKeys } from "@/lib/api";
import { formatDateTime, formatPercent } from "@/lib/format";

export const Route = createFileRoute("/processing/$jobId")({
  head: () => ({
    meta: [
      { title: "Processing — Muse" },
      {
        name: "description",
        content:
          "Watch Muse read a document: parsing, extraction, entity resolution, relationships and timeline placement.",
      },
      { property: "og:title", content: "Processing — Muse" },
      {
        property: "og:description",
        content: "Live progress while Muse turns a document into memory.",
      },
    ],
  }),
  component: ProcessingPage,
});

function ProcessingPage() {
  const { jobId } = Route.useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.processingJob(jobId),
    queryFn: () => museApi.getProcessingJob(jobId),
  });

  if (isLoading) {
    return (
      <AppShell>
        <LoadingState label="Checking the job" />
      </AppShell>
    );
  }

  if (isError || !data) {
    return (
      <AppShell>
        <EmptyState
          title="Job not found"
          description="This processing job is no longer available."
          action={
            <Button asChild>
              <Link to="/library">Open library</Link>
            </Button>
          }
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Step two"
        title={data.documentTitle}
        description={`Started ${formatDateTime(data.startedAt)} · ${formatPercent(data.progress)} complete`}
        actions={
          <Button variant="outline" asChild>
            <Link to="/documents/$documentId" params={{ documentId: data.documentId }}>
              Open document
            </Link>
          </Button>
        }
      />

      <Progress value={data.progress * 100} />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
        <section className="surface-paper rounded-lg p-4">
          <h2 className="mb-2 px-2 text-xl">Pipeline</h2>
          <ProcessingStages stages={data.stages} />
        </section>

        <aside className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Memories" value={data.discovered.memories} />
            <StatCard label="Entities" value={data.discovered.entities} />
            <StatCard label="Links" value={data.discovered.relationships} />
            <StatCard label="Events" value={data.discovered.timelineEvents} />
          </div>

          <div className="surface-paper rounded-lg p-5">
            <h2 className="text-xl">Found so far</h2>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {data.discovered.highlights.map((highlight) => (
                <li key={highlight} className="border-l-2 border-ember/40 pl-3">
                  {highlight}
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
