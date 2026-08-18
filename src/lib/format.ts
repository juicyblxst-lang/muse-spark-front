import type { IsoDateTime } from "@/types/api";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[unit]}`;
}

export function formatDate(value: IsoDateTime | null): string {
  if (!value) return "Undated";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value: IsoDateTime | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function formatYear(value: IsoDateTime | null): string {
  if (!value) return "—";
  return String(new Date(value).getFullYear());
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatRelative(value: IsoDateTime | null): string {
  if (!value) return "Undated";
  const diffDays = Math.round((Date.now() - new Date(value).getTime()) / 86_400_000);
  if (diffDays < 1) return "today";
  if (diffDays < 30) return `${diffDays} days ago`;
  if (diffDays < 365) return `${Math.round(diffDays / 30)} months ago`;
  const years = (diffDays / 365).toFixed(1).replace(/\.0$/, "");
  return `${years} years ago`;
}
