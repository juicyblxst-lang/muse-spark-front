import { Link } from "@tanstack/react-router";
import { FileText, Moon } from "lucide-react";

import { MemoryKindBadge } from "@/components/muse/StatusBadge";
import { formatPercent, formatRelative } from "@/lib/format";
import type { MemorySummary } from "@/types/api";

export function MemoryCard({ memory, reason }: { memory: MemorySummary; reason?: string }) {
  return (
    <article className="surface-paper rounded-lg p-5 transition-shadow hover:shadow-lift">
      <div className="flex flex-wrap items-center gap-2">
        <MemoryKindBadge kind={memory.kind} />
        <span className="text-xs text-muted-foreground">{formatRelative(memory.occurredAt)}</span>
        {memory.dormancy > 0.6 ? (
          <span className="inline-flex items-center gap-1 text-xs text-dormant">
            <Moon className="size-3" /> dormant {formatPercent(memory.dormancy)}
          </span>
        ) : null}
      </div>

      <h3 className="mt-3 text-xl leading-snug">
        <Link to="/memory/$memoryId" params={{ memoryId: memory.id }} className="hover:text-ember">
          {memory.title}
        </Link>
      </h3>

      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{memory.snippet}</p>

      {reason ? (
        <p className="mt-3 border-l-2 border-ember/40 pl-3 text-xs italic text-muted-foreground">
          {reason}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <Link
          to="/documents/$documentId"
          params={{ documentId: memory.documentId }}
          className="inline-flex items-center gap-1 hover:text-ember"
        >
          <FileText className="size-3.5" />
          {memory.documentTitle}
        </Link>
        <span>confidence {formatPercent(memory.confidence)}</span>
        {memory.tags.map((tag) => (
          <span key={tag} className="rounded bg-parchment px-1.5 py-0.5">
            #{tag}
          </span>
        ))}
      </div>
    </article>
  );
}
