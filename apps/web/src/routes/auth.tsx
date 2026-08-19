import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";

import { MuseMark } from "@/components/muse/MuseMark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { museApi } from "@/lib/api";
import { supabaseAuthConfigured } from "@/lib/supabase";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in to Muse" },
      {
        name: "description",
        content: "Sign in or create a Muse account to open your creative memory archive.",
      },
      { property: "og:title", content: "Sign in to Muse" },
      { property: "og:description", content: "Access your Muse creative memory archive." },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const navigate = useNavigate();
  const [pending, setPending] = useState(false);

  async function handleSignIn(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    try {
      await museApi.signIn({
        email: String(form.get("email") ?? ""),
        password: String(form.get("password") ?? ""),
      });
      toast.success("Welcome back");
      await navigate({ to: "/dashboard" });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to sign in");
    } finally {
      setPending(false);
    }
  }

  async function handleSignUp(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    try {
      await museApi.signUp({
        email: String(form.get("email") ?? ""),
        password: String(form.get("password") ?? ""),
        displayName: String(form.get("displayName") ?? ""),
      });
      toast.success("Archive created");
      await navigate({ to: "/upload" });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to create your account");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="bg-archive flex min-h-screen items-center justify-center px-5 py-12">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <MuseMark className="size-8" />
          <span className="text-display text-2xl">Muse</span>
        </Link>

        <h1 className="mb-6 text-center text-3xl">Open your archive</h1>

        <div className="surface-paper rounded-xl p-6 sm:p-8">
          <Tabs defaultValue="signin">
            <TabsList className="w-full">
              <TabsTrigger value="signin" className="flex-1">
                Sign in
              </TabsTrigger>
              <TabsTrigger value="signup" className="flex-1">
                Create account
              </TabsTrigger>
            </TabsList>

            <TabsContent value="signin" className="pt-6">
              <form className="space-y-4" onSubmit={handleSignIn}>
                <div className="space-y-2">
                  <Label htmlFor="signin-email">Email</Label>
                  <Input id="signin-email" name="email" type="email" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signin-password">Password</Label>
                  <Input id="signin-password" name="password" type="password" required />
                </div>
                <Button type="submit" className="w-full" disabled={pending}>
                  {pending ? "Opening archive…" : "Sign in"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup" className="pt-6">
              <form className="space-y-4" onSubmit={handleSignUp}>
                <div className="space-y-2">
                  <Label htmlFor="signup-name">Name</Label>
                  <Input id="signup-name" name="displayName" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input id="signup-email" name="email" type="email" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-password">Password</Label>
                  <Input id="signup-password" name="password" type="password" minLength={6} required />
                </div>
                <Button type="submit" className="w-full" disabled={pending}>
                  {pending ? "Creating…" : "Create archive"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </div>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          {supabaseAuthConfigured
            ? "Your account is secured by Supabase Auth. Sessions persist across browser refreshes."
            : "Supabase Auth is not configured yet. Add the Muse Supabase environment variables to enable real accounts."}
        </p>
      </div>
    </div>
  );
}
