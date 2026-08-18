import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";

import { AppShell } from "@/components/muse/AppShell";
import { LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { museApi, queryKeys } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { CorrectionKind, CorrectionTargetType } from "@/types/api";

export const Route = createFileRoute("/corrections")({
  head: () => ({
    meta: [
      { title: "Corrections — Muse" },
      {
        name: "description",
        content:
          "Tell Muse when it misread something: edit, merge, split, retype or reject anything it remembered.",
      },
      { property: "og:title", content: "Corrections — Muse" },
      {
        property: "og:description",
        content: "Correct Muse's memory so the archive stays true to your material.",
      },
    ],
  }),
  component: CorrectionsPage,
});

const targetTypes: CorrectionTargetType[] = ["memory", "entity", "relationship", "timeline_event"];
const kinds: CorrectionKind[] = ["edit", "merge", "split", "reject", "retype"];

function CorrectionsPage() {
  const queryClient = useQueryClient();
  const [targetType, setTargetType] = useState<CorrectionTargetType>("memory");
  const [kind, setKind] = useState<CorrectionKind>("edit");
  const [targetId, setTargetId] = useState("");
  const [field, setField] = useState("");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.corrections,
    queryFn: () => museApi.listCorrections(),
  });

  const submit = useMutation({
    mutationFn: () =>
      museApi.submitCorrection({
        targetType,
        targetId,
        kind,
        ...(field ? { field } : {}),
        ...(value ? { value } : {}),
        reason,
      }),
    onSuccess: async () => {
      toast.success("Correction submitted");
      setTargetId("");
      setField("");
      setValue("");
      setReason("");
      await queryClient.invalidateQueries({ queryKey: queryKeys.corrections });
    },
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Keep the archive honest"
        title="Corrections"
        description="Muse never overwrites your material, so every fix is recorded as a correction against what it inferred."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <form
          className="surface-paper space-y-4 rounded-lg p-6"
          onSubmit={(event) => {
            event.preventDefault();
            submit.mutate();
          }}
        >
          <h2 className="text-2xl">Submit a correction</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>What is wrong?</Label>
              <Select
                value={targetType}
                onValueChange={(next) => setTargetType(next as CorrectionTargetType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {targetTypes.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option.replace("_", " ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Kind of fix</Label>
              <Select value={kind} onValueChange={(next) => setKind(next as CorrectionKind)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {kinds.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="target-id">Target id</Label>
            <Input
              id="target-id"
              required
              value={targetId}
              onChange={(event) => setTargetId(event.target.value)}
              placeholder="mem_1"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="field">Field (optional)</Label>
              <Input
                id="field"
                value={field}
                onChange={(event) => setField(event.target.value)}
                placeholder="title"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="value">New value (optional)</Label>
              <Input id="value" value={value} onChange={(event) => setValue(event.target.value)} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">Why</Label>
            <Textarea
              id="reason"
              required
              rows={3}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="These two people are the same person."
            />
          </div>

          <Button type="submit" disabled={submit.isPending}>
            {submit.isPending ? "Submitting…" : "Submit correction"}
          </Button>
        </form>

        <section>
          <h2 className="mb-4 text-2xl">History</h2>
          {isLoading || !data ? (
            <LoadingState label="Loading corrections" />
          ) : (
            <ul className="space-y-3">
              {data.map((correction) => (
                <li key={correction.id} className="surface-paper rounded-lg p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{correction.kind}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {correction.targetType.replace("_", " ")} · {correction.targetLabel}
                    </span>
                    <span className="ml-auto text-xs text-muted-foreground">
                      {correction.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm">{correction.reason}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {formatDateTime(correction.submittedAt)}
                    {correction.field ? ` · ${correction.field} → ${correction.value ?? "—"}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </AppShell>
  );
}
