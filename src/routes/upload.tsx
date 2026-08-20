import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { FileUp, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { AppShell } from "@/components/muse/AppShell";
import { PageHeader } from "@/components/muse/PageHeader";
import { Button } from "@/components/ui/button";
import { museApi } from "@/lib/api";
import { formatBytes } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { DocumentKind } from "@/types/api";

export const Route = createFileRoute("/upload")({
  head: () => ({
    meta: [
      { title: "Upload material — Muse" },
      {
        name: "description",
        content: "Add PDFs, DOCX, TXT and Markdown files for Muse to read and remember.",
      },
      { property: "og:title", content: "Upload material — Muse" },
      { property: "og:description", content: "Add old drafts and notebooks to your Muse archive." },
    ],
  }),
  component: UploadPage,
});

const acceptedKinds: Record<string, DocumentKind> = {
  pdf: "pdf",
  docx: "docx",
  txt: "txt",
  md: "md",
  markdown: "md",
};

interface Queued {
  id: string;
  name: string;
  sizeBytes: number;
  kind: DocumentKind;
  file: File;
}

function toQueued(file: File): Queued | null {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  const kind = acceptedKinds[extension];
  if (!kind) return null;
  return {
    id: `${file.name}-${file.size}-${Math.random().toString(36).slice(2, 6)}`,
    name: file.name,
    sizeBytes: file.size,
    kind,
    file,
  };
}

function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<Queued[]>([]);
  const [sending, setSending] = useState(false);

  function addFiles(files: FileList | null) {
    if (!files) return;
    const accepted: Queued[] = [];
    let rejected = 0;
    for (const file of Array.from(files)) {
      const queued = toQueued(file);
      if (queued) accepted.push(queued);
      else rejected += 1;
    }
    if (rejected > 0) toast.error(`${rejected} file(s) skipped — PDF, DOCX, TXT and MD only`);
    if (accepted.length > 0) setQueue((current) => [...current, ...accepted]);
  }

  async function submit() {
    if (queue.length === 0) return;
    setSending(true);
    try {
      const uploads = await Promise.all(
        queue.map(async (item) => {
          const target = await museApi.createUpload({
            fileName: item.name,
            kind: item.kind,
            sizeBytes: item.sizeBytes,
          });
          const response = await fetch(target.uploadUrl, {
            method: "PUT",
            headers: item.file.type ? { "content-type": item.file.type } : undefined,
            body: item.file,
          });
          if (!response.ok) {
            throw new Error("Muse upload failed (" + response.status + ")");
          }
          return target;
        }),
      );
      const first = uploads[0];
      toast.success(`${queue.length} file(s) handed to Muse`);
      setQueue([]);
      if (first) await navigate({ to: "/processing/$jobId", params: { jobId: first.jobId } });
    } finally {
      setSending(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Step one"
        title="Give Muse something to remember"
        description="Old treatments, studio notebooks, half-written proposals. Muse reads each file once and keeps what it finds."
      />

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          addFiles(event.dataTransfer.files);
        }}
        className={cn(
          "surface-paper flex flex-col items-center rounded-xl border-dashed px-6 py-16 text-center transition-colors",
          dragging && "bg-ember/8 border-ember",
        )}
      >
        <FileUp className="mb-4 size-8 text-ember" />
        <h2 className="text-2xl">Drop files here</h2>
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">
          PDF, DOCX, TXT and Markdown. Nothing is uploaded in this preview — the file list is handed
          to the upload contract only.
        </p>
        <Button className="mt-6" variant="outline" onClick={() => inputRef.current?.click()}>
          Choose files
        </Button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md,.markdown"
          className="hidden"
          onChange={(event) => addFiles(event.target.files)}
        />
      </div>

      {queue.length > 0 ? (
        <section className="mt-8">
          <h2 className="mb-4 text-2xl">Ready to process</h2>
          <ul className="space-y-2">
            {queue.map((item) => (
              <li
                key={item.id}
                className="surface-paper flex items-center gap-4 rounded-lg px-4 py-3"
              >
                <span className="min-w-0 flex-1 truncate text-sm">{item.name}</span>
                <span className="text-xs uppercase text-muted-foreground">{item.kind}</span>
                <span className="text-xs text-muted-foreground">{formatBytes(item.sizeBytes)}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Remove ${item.name}`}
                  onClick={() => setQueue((current) => current.filter((q) => q.id !== item.id))}
                >
                  <Trash2 className="size-4" />
                </Button>
              </li>
            ))}
          </ul>
          <Button className="mt-5" size="lg" onClick={submit} disabled={sending}>
            {sending ? "Handing to Muse…" : `Process ${queue.length} file(s)`}
          </Button>
        </section>
      ) : null}
    </AppShell>
  );
}
