import { Link } from "@tanstack/react-router";
import { Quote } from "lucide-react";

import type { SourceReference } from "@/types/api";

export function SourceList({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) {
    return <p className="text-sm text-muted-foreground">No source passages recorded.</p>;
  }

  return (
    <ul className="space-y-3">
      {sources.map((source) => (
        <li key={source.id} className="surface-paper rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Quote className="mt-1 size-4 shrink-0 text-ember" />
            <div className="min-w-0">
              <p className="text-sm italic leading-relaxed">“{source.quote}”</p>
              <p className="mt-2 text-xs text-muted-foreground">
                {source.documentTitle}
                {source.page ? ` · page ${source.page}` : ""}
                {source.charStart !== null ? ` · chars ${source.charStart}–${source.charEnd}` : ""}
              </p>
              <Link
                to="/provenance/$sourceId"
                params={{ sourceId: source.id }}
                className="mt-2 inline-block text-xs text-ember hover:underline"
              >
                View provenance
              </Link>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
