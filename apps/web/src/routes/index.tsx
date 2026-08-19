import { Link, createFileRoute } from "@tanstack/react-router";
import { ArrowRight, Clock3, FileStack, Network, Search, Sparkles, Upload } from "lucide-react";

import { MuseMark } from "@/components/muse/MuseMark";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Muse — Creative memory for abandoned ideas" },
      {
        name: "description",
        content:
          "Muse remembers your old creative material — treatments, notebooks, drafts — and helps you rediscover and revive the ideas you abandoned.",
      },
      { property: "og:title", content: "Muse — Creative memory for abandoned ideas" },
      {
        property: "og:description",
        content:
          "Upload old drafts and notebooks. Muse remembers the ideas, people and timelines, then helps you revive what you forgot.",
      },
    ],
  }),
  component: Landing,
});

const steps = [
  {
    icon: Upload,
    title: "Upload material",
    body: "PDFs, DOCX, TXT and Markdown from any era of your practice.",
  },
  {
    icon: FileStack,
    title: "Muse processes it",
    body: "Each document is read once and turned into durable memory.",
  },
  {
    icon: Search,
    title: "See what surfaced",
    body: "Ideas, entities, relationships and dates, each traceable to its source.",
  },
  {
    icon: Clock3,
    title: "Search your past",
    body: "Ask in your own words and get passages you no longer remember writing.",
  },
  {
    icon: Network,
    title: "Muse resurfaces",
    body: "Dormant work is brought back when it connects to something current.",
  },
  {
    icon: Sparkles,
    title: "Revive an idea",
    body: "Ask for next steps, a reframe, or two fragments combined into one.",
  },
];

function Landing() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <MuseMark className="size-8" />
          <span className="text-display text-2xl">Muse</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" asChild>
            <Link to="/auth">Sign in</Link>
          </Button>
          <Button asChild>
            <Link to="/dashboard">Open Muse</Link>
          </Button>
        </div>
      </header>

      <section className="bg-archive border-b border-border">
        <div className="mx-auto w-full max-w-6xl px-6 py-20 sm:py-28">
          <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
            Creative memory
          </p>
          <h1 className="mt-5 max-w-3xl text-5xl leading-[1.05] sm:text-6xl">
            Your best ideas are already written down. You just don't remember where.
          </h1>
          <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground">
            Muse reads the drafts, notebooks and proposals you abandoned, remembers the ideas and
            the people and the dates, and brings them back when they matter again.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Button size="lg" asChild>
              <Link to="/upload">
                Upload your archive <ArrowRight className="ml-1 size-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/memory">Search a memory</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-6 py-20">
        <h2 className="text-3xl">How Muse works</h2>
        <p className="mt-3 max-w-xl text-sm text-muted-foreground">
          One loop, repeated: material in, memory out, forgotten work back on your desk.
        </p>
        <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map((step, index) => (
            <li key={step.title} className="surface-paper rounded-lg p-5">
              <div className="flex items-center justify-between">
                <step.icon className="size-5 text-ember" />
                <span className="text-display text-2xl text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>
              <h3 className="mt-4 text-xl">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-t border-border bg-parchment">
        <div className="mx-auto w-full max-w-6xl px-6 py-16">
          <div className="bg-ember-wash surface-paper rounded-xl p-8 sm:p-12">
            <h2 className="max-w-xl text-3xl">Nothing you made is lost. It is only unindexed.</h2>
            <Button className="mt-7" size="lg" asChild>
              <Link to="/auth">Create your archive</Link>
            </Button>
          </div>
        </div>
      </section>

      <footer className="mx-auto w-full max-w-6xl px-6 py-10 text-xs text-muted-foreground">
        Muse — creative memory. Frontend preview with mock data.
      </footer>
    </div>
  );
}
