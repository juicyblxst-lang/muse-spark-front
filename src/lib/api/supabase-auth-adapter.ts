import type { MuseApi, Session, SignInRequest, SignUpRequest, User } from "@/types/api";
import { supabase } from "@/lib/supabase";

function toMuseUser(user: {
  id: string;
  email?: string | null;
  created_at?: string;
  user_metadata?: Record<string, unknown>;
}): User {
  const metadata = user.user_metadata ?? {};
  const displayName =
    typeof metadata.displayName === "string" && metadata.displayName.trim()
      ? metadata.displayName
      : typeof metadata.full_name === "string" && metadata.full_name.trim()
        ? metadata.full_name
        : user.email?.split("@")[0] ?? "Muse user";

  return {
    id: user.id,
    email: user.email ?? "",
    displayName,
    avatarUrl: typeof metadata.avatar_url === "string" ? metadata.avatar_url : null,
    createdAt: user.created_at ?? new Date().toISOString(),
  };
}

async function currentSession(): Promise<Session> {
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  if (!data.session) throw new Error("No active Muse session.");

  const user = toMuseUser(data.session.user);
  return {
    token: data.session.access_token,
    expiresAt: new Date(data.session.expires_at * 1000).toISOString(),
    user,
  };
}

export const supabaseAuthApi: Pick<
  MuseApi,
  "signIn" | "signUp" | "signOut" | "getCurrentUser"
> = {
  async signIn(input: SignInRequest) {
    const { error } = await supabase.auth.signInWithPassword({
      email: input.email.trim(),
      password: input.password,
    });
    if (error) throw error;
    return currentSession();
  },

  async signUp(input: SignUpRequest) {
    const { data, error } = await supabase.auth.signUp({
      email: input.email.trim(),
      password: input.password,
      options: {
        data: {
          displayName: input.displayName.trim(),
        },
      },
    });
    if (error) throw error;

    // Supabase may require email confirmation. In that case there is no session yet.
    if (!data.session) {
      throw new Error("Account created. Check your email to confirm your address, then sign in.");
    }

    return currentSession();
  },

  async signOut() {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  async getCurrentUser() {
    const { data, error } = await supabase.auth.getUser();
    if (error) {
      // An expired/missing session is a normal signed-out state.
      if (error.message.toLowerCase().includes("auth session missing")) return null;
      throw error;
    }
    return data.user ? toMuseUser(data.user) : null;
  },
};
