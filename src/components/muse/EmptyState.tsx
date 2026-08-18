import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="surface-paper flex flex-col items-center rounded-lg px-6 py-14 text-center">
      {Icon ? <Icon className="mb-4 size-7 text-ember" /> : null}
      <h3 className="text-xl">{title}</h3>
      {description ? (
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="surface-paper rounded-lg px-6 py-14 text-center text-sm text-muted-foreground">
      {label}…
    </div>
  );
}
