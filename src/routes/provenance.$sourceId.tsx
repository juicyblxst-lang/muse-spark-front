import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { Button } from "@/components/ui/button";
import { museApi, queryKeys } from "@/lib/api";
import { formatDateTime, formatPercent } from "@/lib/format";

export const Route = createFileRoute("/provenance/$sourceId")({
  head: () => ({
    meta: [
      { title: "Provenance — Muse" },
      {
        name: "description",
        content:
          "The exact passage a memory came from, with offsets, extraction time and derived memories.",
      },
      { property: "og:title", content: "Provenance — Muse" },
      {
        property: "og:description",
        content: "Trace any Muse memory back to the original wording in your document.",
      },
    ],
  }),
  component: ProvenancePage,
});

function ProvenancePage() {
  const { sourceId } = Route.useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.provenance(sourceId),
    queryFn: () => museApi.getProvenance(sourceId),
  });

  if (isLoading) {
    return (
      <AppShell>
        <LoadingState label="Locating the passage" />
      </AppShell>
    );
  }

  if (isError || !data) {
    return (
      <AppShell>
        <EmptyState
          title="Source not found"
          action={
            <Button asChild>
              <Link to="/library">Back to library</Link>
            </Button>
          }
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Provenance"
        title={data.source.documentTitle}
        description={`Extracted ${formatDateTime(data.extractedAt)} · confidence ${formatPercent(
          data.confidence,
        )} · ${data.extractorVersion}`}
        actions={
          <Button variant="outline" asChild>
            <Link to="/documents/$documentId" params={{ documentId: data.source.documentId }}>
              Open document
            </Link>
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="space-y-6">
          <section className="surface-paper rounded-lg p-6">
            <h2 className="text-xl">Quoted passage</h2>
            <blockquote className="mt-3 border-l-2 border-ember pl-4 text-base italic leading-relaxed">
              {data.source.quote}
            </blockquote>
          </section>

          <section className="surface-paper rounded-lg p-6">
            <h2 className="text-xl">Surrounding context as parsed</h2>
            <p className="mt-3 font-mono text-sm leading-relaxed text-muted-foreground">
              {data.context}
            </p>
          </section>
        </div>

        <aside className="space-y-4">
          <div className="surface-paper rounded-lg p-5 text-sm text-muted-foreground">
            <p>Format: {data.source.kind.toUpperCase()}</p>
            <p>Page: {data.source.page ?? "—"}</p>
            <p>
              Offsets: {data.source.charStart ?? "—"} – {data.source.charEnd ?? "—"}
            </p>
          </div>

          <div className="surface-paper rounded-lg p-5">
            <h2 className="text-xl">Derived memories</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {data.derivedMemoryIds.map((id) => (
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
            <Link to="/corrections">Report a mis-read</Link>
          </Button>
        </aside>
      </div>
    </AppShell>
  );
}
