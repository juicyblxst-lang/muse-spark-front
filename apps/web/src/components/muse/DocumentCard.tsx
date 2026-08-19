import { Link } from "@tanstack/react-router";
import { FileCode2, FileText, FileType2 } from "lucide-react";

import { DocumentStatusBadge } from "@/components/muse/StatusBadge";
import { formatBytes, formatDate } from "@/lib/format";
import type { DocumentKind, DocumentSummary } from "@/types/api";

const kindIcon: Record<DocumentKind, typeof FileText> = {
  pdf: FileType2,
  docx: FileText,
  txt: FileText,
  md: FileCode2,
};

export function DocumentCard({ document }: { document: DocumentSummary }) {
  const Icon = kindIcon[document.kind];

  return (
    <article className="surface-paper flex flex-wrap items-center gap-4 rounded-lg p-4">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-parchment">
        <Icon className="size-5 text-ember" />
      </span>

      <div className="min-w-0 flex-1">
        <h3 className="truncate text-lg leading-tight">
          <Link
            to="/documents/$documentId"
            params={{ documentId: document.id }}
            className="hover:text-ember"
          >
            {document.title}
          </Link>
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {formatBytes(document.sizeBytes)} · uploaded {formatDate(document.uploadedAt)} · authored{" "}
          {formatDate(document.authoredAt)}
        </p>
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span>{document.memoryCount} memories</span>
        <span>{document.entityCount} entities</span>
        <DocumentStatusBadge status={document.status} />
      </div>
    </article>
  );
}
