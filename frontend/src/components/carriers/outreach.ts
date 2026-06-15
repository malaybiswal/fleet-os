// Shared outreach pipeline constants and helpers used by the carrier detail page,
// the demo cards, and the CRM board so labels, colors, and ordering stay in sync.

export type OutreachStatus =
  | "not_contacted"
  | "contacted"
  | "follow_up"
  | "not_interested"
  | "converted";

export const OUTREACH_OPTIONS: { value: OutreachStatus; label: string }[] = [
  { value: "not_contacted", label: "Not Contacted" },
  { value: "contacted", label: "Contacted" },
  { value: "follow_up", label: "Follow Up" },
  { value: "not_interested", label: "Not Interested" },
  { value: "converted", label: "Converted" },
];

// Pipeline column order for the CRM board.
export const OUTREACH_ORDER: OutreachStatus[] = OUTREACH_OPTIONS.map((o) => o.value);

export const OUTREACH_STYLES: Record<string, string> = {
  not_contacted: "bg-slate-100 text-slate-600",
  contacted: "bg-blue-100 text-blue-700",
  follow_up: "bg-yellow-100 text-yellow-700",
  not_interested: "bg-red-100 text-red-600",
  converted: "bg-emerald-100 text-emerald-700",
};

export function outreachLabel(status: string): string {
  return OUTREACH_OPTIONS.find((o) => o.value === status)?.label ?? status;
}

// Compact relative time for the "last contacted" badge, e.g. "today", "3d ago".
export function relativeContactTime(iso: string | null): string | null {
  if (!iso) return null;
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}
