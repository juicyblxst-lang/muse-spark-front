import { cn } from "@/lib/utils";

export function MuseMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" role="img" aria-label="Muse" className={cn("text-ember", className)}>
      <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="1.25" />
      <path
        d="M8 21c2.5-9 5-9 8-2s5.5 5 8-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <circle cx="16" cy="16" r="2.2" fill="currentColor" />
    </svg>
  );
}
