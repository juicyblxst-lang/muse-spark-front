import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { AppShell } from "@/components/muse/AppShell";
import { LoadingState } from "@/components/muse/EmptyState";
import { PageHeader } from "@/components/muse/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { museApi, queryKeys } from "@/lib/api";
import type { SettingsUpdate } from "@/types/api";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — Muse" },
      {
        name: "description",
        content:
          "Tune how dormant an idea must be before Muse resurfaces it, plus processing and notification preferences.",
      },
      { property: "og:title", content: "Settings — Muse" },
      {
        property: "og:description",
        content: "Control resurfacing thresholds, processing options and notifications.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.settings,
    queryFn: () => museApi.getSettings(),
  });

  const update = useMutation({
    mutationFn: (input: SettingsUpdate) => museApi.updateSettings(input),
    onSuccess: async (settings) => {
      queryClient.setQueryData(queryKeys.settings, settings);
      toast.success("Settings saved");
    },
  });

  async function signOut() {
    await museApi.signOut();
    toast.success("Signed out");
    await navigate({ to: "/auth" });
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Preferences"
        title="Settings"
        description="How Muse reads new material and when it decides an idea has gone quiet."
      />

      {isLoading || !data ? (
        <LoadingState label="Loading settings" />
      ) : (
        <div className="space-y-6">
          <section className="surface-paper rounded-lg p-6">
            <h2 className="text-2xl">Profile</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="displayName">Name</Label>
                <Input
                  id="displayName"
                  defaultValue={data.profile.displayName}
                  onBlur={(event) =>
                    update.mutate({ profile: { displayName: event.target.value } })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" defaultValue={data.profile.email} readOnly />
              </div>
            </div>
          </section>

          <section className="surface-paper rounded-lg p-6">
            <h2 className="text-2xl">Memory</h2>

            <div className="mt-5 space-y-3">
              <Label>Dormancy threshold: {data.memory.dormancyThresholdDays} days</Label>
              <Slider
                value={[data.memory.dormancyThresholdDays]}
                min={30}
                max={730}
                step={30}
                onValueChange={([next]) =>
                  update.mutate({ memory: { dormancyThresholdDays: next ?? 180 } })
                }
              />
              <p className="text-xs text-muted-foreground">
                Material untouched for longer than this is treated as forgotten.
              </p>
            </div>

            <div className="mt-6 space-y-3">
              <Label>Minimum confidence: {Math.round(data.memory.minConfidence * 100)}%</Label>
              <Slider
                value={[data.memory.minConfidence * 100]}
                min={0}
                max={100}
                step={5}
                onValueChange={([next]) =>
                  update.mutate({ memory: { minConfidence: (next ?? 60) / 100 } })
                }
              />
              <p className="text-xs text-muted-foreground">
                Extractions below this confidence stay hidden until you confirm them.
              </p>
            </div>

            <div className="mt-6 flex items-center justify-between gap-4">
              <div>
                <Label>Auto-resurface</Label>
                <p className="text-xs text-muted-foreground">
                  Let Muse bring dormant work back on its own.
                </p>
              </div>
              <Switch
                checked={data.memory.autoResurfaceEnabled}
                onCheckedChange={(checked) =>
                  update.mutate({ memory: { autoResurfaceEnabled: checked } })
                }
              />
            </div>
          </section>

          <section className="surface-paper rounded-lg p-6">
            <h2 className="text-2xl">Processing</h2>
            <div className="mt-5 space-y-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <Label>OCR scanned pages</Label>
                  <p className="text-xs text-muted-foreground">
                    For PDFs that contain images of text.
                  </p>
                </div>
                <Switch
                  checked={data.processing.ocrEnabled}
                  onCheckedChange={(checked) =>
                    update.mutate({ processing: { ocrEnabled: checked } })
                  }
                />
              </div>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <Label>Retain original files</Label>
                  <p className="text-xs text-muted-foreground">Required for provenance views.</p>
                </div>
                <Switch
                  checked={data.processing.retainOriginals}
                  onCheckedChange={(checked) =>
                    update.mutate({ processing: { retainOriginals: checked } })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="languageHint">Language hint</Label>
                <Input
                  id="languageHint"
                  defaultValue={data.processing.languageHint}
                  onBlur={(event) =>
                    update.mutate({ processing: { languageHint: event.target.value } })
                  }
                  className="max-w-32"
                />
              </div>
            </div>
          </section>

          <section className="surface-paper rounded-lg p-6">
            <h2 className="text-2xl">Notifications</h2>
            <div className="mt-5 space-y-5">
              <div className="flex items-center justify-between gap-4">
                <Label>Processing complete</Label>
                <Switch
                  checked={data.notifications.processingComplete}
                  onCheckedChange={(checked) =>
                    update.mutate({ notifications: { processingComplete: checked } })
                  }
                />
              </div>
              <div className="flex items-center justify-between gap-4">
                <Label>Weekly resurfacing digest</Label>
                <Switch
                  checked={data.notifications.weeklyResurfacing}
                  onCheckedChange={(checked) =>
                    update.mutate({ notifications: { weeklyResurfacing: checked } })
                  }
                />
              </div>
            </div>
          </section>

          <Button variant="outline" onClick={signOut}>
            Sign out
          </Button>
        </div>
      )}
    </AppShell>
  );
}
