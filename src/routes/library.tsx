import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { FileStack, Upload } from "lucide-react";
import { useState } from "react";

import { AppShell } from "@/components/muse/AppShell";
import { DocumentCard } from "@/components/muse/DocumentCard";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { museApi, queryKeys } from "@/lib/api";
import type { DocumentStatus } from "@/types/api";

export const Route = createFileRoute("/library")({
  head: () => ({
    meta: [
      { title: "Document library — Muse" },
      {
        name: "description",
        content:
          "Every file Muse has read, with processing status, memory counts and original dates.",
      },
      { property: "og:title", content: "Document library — Muse" },
      {
        property: "og:description",
        content: "Browse the source material behind your creative memory.",
      },
    ],
  }),
  component: LibraryPage,
});

const statuses: Array<DocumentStatus | "all"> = [
  "all",
  "ready",
  "processing",
  "needs_review",
  "queued",
  "failed",
];

function LibraryPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<DocumentStatus | "all">("all");

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.documents(`${query}|${status}`),
    queryFn: () =>
      museApi.listDocuments({
        query: query || undefined,
        status: status === "all" ? undefined : status,
      }),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Source material"
        title="Document library"
        description="The files behind every memory. Each one keeps its original date so Muse can place it in time."
        actions={
          <Button asChild>
            <Link to="/upload">
              <Upload className="mr-1 size-4" /> Upload
            </Link>
          </Button>
        }
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <Input
          placeholder="Search titles and tags"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="max-w-xs"
        />
        <Select
          value={status}
          onValueChange={(value) => setStatus(value as DocumentStatus | "all")}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {statuses.map((option) => (
              <SelectItem key={option} value={option}>
                {option === "all" ? "All statuses" : option.replace("_", " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <LoadingState label="Opening the library" />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={FileStack}
          title="Nothing here yet"
          description="Upload a PDF, DOCX, TXT or Markdown file and Muse will start remembering."
          action={
            <Button asChild>
              <Link to="/upload">Upload material</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">{data.total} document(s)</p>
          {data.items.map((document) => (
            <DocumentCard key={document.id} document={document} />
          ))}
        </div>
      )}
    </AppShell>
  );
}
