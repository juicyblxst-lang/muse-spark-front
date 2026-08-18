import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { FileStack, Moon, Network, Sparkles, Upload, Users } from "lucide-react";

import { AppShell } from "@/components/muse/AppShell";
import { DocumentCard } from "@/components/muse/DocumentCard";
import { LoadingState } from "@/components/muse/EmptyState";
import { MemoryCard } from "@/components/muse/MemoryCard";
import { PageHeader } from "@/components/muse/PageHeader";
import { StatCard } from "@/components/muse/StatCard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { museApi, queryKeys } from "@/lib/api";
import { formatPercent } from "@/lib/format";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Muse" },
      {
        name: "description",
        content:
          "Your archive at a glance: processing jobs, recent uploads and dormant ideas Muse wants to resurface.",
      },
      { property: "og:title", content: "Dashboard — Muse" },
      {
        property: "og:description",
        content: "Processing jobs, recent uploads and dormant ideas in your Muse archive.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: () => museApi.getDashboard(),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Your archive"
        title="What Muse remembers"
        description="Everything Muse has read, plus the material it thinks you have forgotten."
        actions={
          <Button asChild>
            <Link to="/upload">
              <Upload className="mr-1 size-4" /> Upload material
            </Link>
          </Button>
        }
      />

      {isLoading || !data ? (
        <LoadingState label="Reading your archive" />
      ) : (
        <div className="space-y-10">
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard label="Documents" value={data.stats.documents} icon={FileStack} />
            <StatCard label="Memories" value={data.stats.memories} icon={Sparkles} />
            <StatCard label="Entities" value={data.stats.entities} icon={Users} />
            <StatCard label="Relationships" value={data.stats.relationships} icon={Network} />
            <StatCard
              label="Dormant"
              value={data.stats.dormantMemories}
              icon={Moon}
              hint="Untouched past your threshold"
            />
          </section>

          {data.activeJobs.length > 0 ? (
            <section>
              <h2 className="mb-4 text-2xl">Processing now</h2>
              <div className="space-y-3">
                {data.activeJobs.map((job) => (
                  <div key={job.id} className="surface-paper rounded-lg p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h3 className="text-lg">{job.documentTitle}</h3>
                        <p className="text-xs text-muted-foreground">
                          {job.currentStage.replace(/_/g, " ")} · {formatPercent(job.progress)}
                        </p>
                      </div>
                      <Button variant="outline" size="sm" asChild>
                        <Link to="/processing/$jobId" params={{ jobId: job.id }}>
                          Watch progress
                        </Link>
                      </Button>
                    </div>
                    <Progress value={job.progress * 100} className="mt-4" />
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          <section>
            <div className="mb-4 flex items-end justify-between">
              <h2 className="text-2xl">Muse thinks you forgot these</h2>
              <Link to="/memory" className="text-sm text-ember hover:underline">
                Search memory
              </Link>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {data.forgotten.map((memory) => (
                <MemoryCard key={memory.id} memory={memory} />
              ))}
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-end justify-between">
              <h2 className="text-2xl">Recent material</h2>
              <Link to="/library" className="text-sm text-ember hover:underline">
                Open library
              </Link>
            </div>
            <div className="space-y-3">
              {data.recentDocuments.map((document) => (
                <DocumentCard key={document.id} document={document} />
              ))}
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-end justify-between">
              <h2 className="text-2xl">Recent revivals</h2>
              <Link to="/revivals" className="text-sm text-ember hover:underline">
                All revivals
              </Link>
            </div>
            <div className="space-y-3">
              {data.recentRevivals.map((revival) => (
                <Link
                  key={revival.id}
                  to="/revivals/$revivalId"
                  params={{ revivalId: revival.id }}
                  className="surface-paper block rounded-lg p-5 hover:shadow-lift"
                >
                  <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
                    {revival.intent.replace("_", " ")}
                  </p>
                  <h3 className="mt-2 text-lg">{revival.memoryTitle}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{revival.summary}</p>
                </Link>
              ))}
            </div>
          </section>
        </div>
      )}
    </AppShell>
  );
}
