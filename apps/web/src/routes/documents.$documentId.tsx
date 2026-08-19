import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { MemoryCard } from "@/components/muse/MemoryCard";
import { PageHeader } from "@/components/muse/PageHeader";
import { ProcessingStages } from "@/components/muse/ProcessingStages";
import { DocumentStatusBadge } from "@/components/muse/StatusBadge";
import { Button } from "@/components/ui/button";
import { museApi, queryKeys } from "@/lib/api";
import { mockMemories } from "@/lib/api/mock-data";
import { formatBytes, formatDate } from "@/lib/format";

export const Route = createFileRoute("/documents/$documentId")({
  head: () => ({
    meta: [
      { title: "Document — Muse" },
      {
        name: "description",
        content:
          "What Muse extracted from this document: memories, entities and the passages they came from.",
      },
      { property: "og:title", content: "Document — Muse" },
      {
        property: "og:description",
        content: "Memories and entities extracted from a single source document.",
      },
    ],
  }),
  component: DocumentDetailPage,
});

function DocumentDetailPage() {
  const { documentId } = Route.useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.document(documentId),
    queryFn: () => museApi.getDocument(documentId),
  });

  if (isLoading) {
    return (
      <AppShell>
        <LoadingState label="Opening the document" />
      </AppShell>
    );
  }

  if (isError || !data) {
    return (
      <AppShell>
        <EmptyState
          title="Document not found"
          action={
            <Button asChild>
              <Link to="/library">Back to library</Link>
            </Button>
          }
        />
      </AppShell>
    );
  }

  const memories = mockMemories.filter((memory) => data.memoryIds.includes(memory.id));

  return (
    <AppShell>
      <PageHeader
        eyebrow="Source document"
        title={data.title}
        description={`${data.kind.toUpperCase()} · ${formatBytes(data.sizeBytes)} · authored ${formatDate(
          data.authoredAt,
        )} · uploaded ${formatDate(data.uploadedAt)}`}
        actions={<DocumentStatusBadge status={data.status} />}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="space-y-8">
          <section className="surface-paper rounded-lg p-5">
            <h2 className="text-xl">Excerpt as parsed</h2>
            <p className="mt-3 text-sm italic leading-relaxed text-muted-foreground">
              {data.excerpt}
            </p>
          </section>

          {data.processing ? (
            <section className="surface-paper rounded-lg p-4">
              <h2 className="mb-2 px-2 text-xl">Processing</h2>
              <ProcessingStages stages={data.processing.stages} />
              <div className="px-2 pt-2">
                <Button variant="outline" size="sm" asChild>
                  <Link to="/processing/$jobId" params={{ jobId: data.processing.id }}>
                    Watch progress
                  </Link>
                </Button>
              </div>
            </section>
          ) : null}

          <section>
            <h2 className="mb-4 text-2xl">Memories from this document</h2>
            {memories.length === 0 ? (
              <EmptyState
                title="No memories yet"
                description="Muse has not finished reading this file, or nothing was extractable."
              />
            ) : (
              <div className="space-y-3">
                {memories.map((memory) => (
                  <MemoryCard key={memory.id} memory={memory} />
                ))}
              </div>
            )}
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
            <Button variant="outline" size="sm" className="mt-4 w-full" asChild>
              <Link to="/connections">See connections</Link>
            </Button>
          </div>

          <div className="surface-paper rounded-lg p-5 text-sm text-muted-foreground">
            <p>Language: {data.language}</p>
            <p>Pages: {data.pageCount ?? "—"}</p>
            <p>Memories: {data.memoryCount}</p>
            <p>Entities: {data.entityCount}</p>
          </div>

          <Button variant="outline" className="w-full" asChild>
            <Link to="/corrections">Something wrong? Correct it</Link>
          </Button>
        </aside>
      </div>
    </AppShell>
  );
}
