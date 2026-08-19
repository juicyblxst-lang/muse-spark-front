import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useState } from "react";

import { AppShell } from "@/components/muse/AppShell";
import { EmptyState, LoadingState } from "@/components/muse/EmptyState";
import { MemoryCard } from "@/components/muse/MemoryCard";
import { PageHeader } from "@/components/muse/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { museApi, queryKeys } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { MemoryKind } from "@/types/api";

export const Route = createFileRoute("/memory/")({
  head: () => ({
    meta: [
      { title: "Search your memory — Muse" },
      {
        name: "description",
        content:
          "Ask Muse in your own words and get back the ideas, notes and fragments you had forgotten writing.",
      },
      { property: "og:title", content: "Search your memory — Muse" },
      {
        property: "og:description",
        content: "Search across everything Muse remembers from your creative archive.",
      },
    ],
  }),
  component: MemorySearchPage,
});

const kinds: MemoryKind[] = ["idea", "note", "decision", "question", "fragment", "plan"];

function MemorySearchPage() {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [activeKinds, setActiveKinds] = useState<MemoryKind[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.memorySearch(`${query}|${activeKinds.join(",")}`),
    queryFn: () =>
      museApi.searchMemories({
        query,
        kinds: activeKinds.length > 0 ? activeKinds : undefined,
      }),
  });

  function toggleKind(kind: MemoryKind) {
    setActiveKinds((current) =>
      current.includes(kind) ? current.filter((k) => k !== kind) : [...current, kind],
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Step four"
        title="Search your memory"
        description="Ask the way you would ask a collaborator who read everything you ever wrote."
      />

      <form
        className="mb-4 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(input);
        }}
      >
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="e.g. that idea about salt, or slow light"
          className="min-w-0 flex-1"
        />
        <Button type="submit">
          <Search className="mr-1 size-4" /> Search
        </Button>
      </form>

      <div className="mb-6 flex flex-wrap gap-2">
        {kinds.map((kind) => (
          <button
            key={kind}
            type="button"
            onClick={() => toggleKind(kind)}
            className={cn(
              "rounded-full border border-border px-3 py-1 text-xs transition-colors",
              activeKinds.includes(kind)
                ? "bg-ember text-ember-foreground border-transparent"
                : "bg-card text-muted-foreground hover:bg-accent",
            )}
          >
            {kind}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingState label="Searching memory" />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={Search}
          title="Nothing matched"
          description="Try a looser phrase — Muse keeps the original wording of your material."
        />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span>{data.total} result(s)</span>
            {data.suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setInput(suggestion);
                  setQuery(suggestion);
                }}
                className="rounded bg-parchment px-2 py-0.5 hover:text-ember"
              >
                {suggestion}
              </button>
            ))}
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {data.items.map((result) => (
              <MemoryCard key={result.memory.id} memory={result.memory} reason={result.reason} />
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
