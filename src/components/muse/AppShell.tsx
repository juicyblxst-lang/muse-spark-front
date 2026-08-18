import { Link, useRouterState } from "@tanstack/react-router";
import {
  Clock3,
  FileStack,
  LayoutDashboard,
  Menu,
  Network,
  Search,
  Settings as SettingsIcon,
  Sparkles,
  SquarePen,
  Upload,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { MuseMark } from "@/components/muse/MuseMark";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/library", label: "Library", icon: FileStack },
  { to: "/memory", label: "Memory", icon: Search },
  { to: "/timeline", label: "Timeline", icon: Clock3 },
  { to: "/connections", label: "Connections", icon: Network },
  { to: "/revivals", label: "Revivals", icon: Sparkles },
  { to: "/corrections", label: "Corrections", icon: SquarePen },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (state) => state.location.pathname });

  return (
    <div className="min-h-screen bg-background lg:grid lg:grid-cols-[248px_1fr]">
      <aside
        className={cn(
          "border-b border-border bg-sidebar lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r",
        )}
      >
        <div className="flex items-center justify-between px-5 py-4">
          <Link to="/" className="flex items-center gap-2">
            <MuseMark className="size-7" />
            <span className="text-display text-xl">Muse</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            aria-label="Toggle navigation"
            onClick={() => setOpen((value) => !value)}
          >
            <Menu className="size-5" />
          </Button>
        </div>

        <nav className={cn("flex-col gap-1 px-3 pb-5 lg:flex", open ? "flex" : "hidden")}>
          {navItems.map((item) => {
            const active = pathname === item.to || pathname.startsWith(`${item.to}/`);
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                )}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="min-w-0 px-5 py-8 sm:px-8 lg:px-12">
        <div className="mx-auto w-full max-w-5xl">{children}</div>
      </main>
    </div>
  );
}
