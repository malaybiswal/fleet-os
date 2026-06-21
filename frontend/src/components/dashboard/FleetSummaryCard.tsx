import type { Truck } from "@/types";

const STATUS_CONFIG = [
  {
    key: "moving",
    label: "Moving",
    dot: "bg-emerald-500",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
  },
  {
    key: "slow",
    label: "Slow",
    dot: "bg-amber-500",
    text: "text-amber-700",
    bg: "bg-amber-50",
  },
  {
    key: "idle",
    label: "Idle",
    dot: "bg-blue-500",
    text: "text-blue-700",
    bg: "bg-blue-50",
  },
  {
    key: "stopped",
    label: "Stopped",
    dot: "bg-slate-500",
    text: "text-slate-700",
    bg: "bg-slate-50",
  },
  {
    key: "maintenance",
    label: "Maintenance",
    dot: "bg-red-500",
    text: "text-red-700",
    bg: "bg-red-50",
  },
];

export function FleetSummaryCard({ trucks }: { trucks: Truck[] }) {
  const counts = trucks.reduce<Record<string, number>>((acc, t) => {
    acc[t.status] = (acc[t.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="rounded-card border border-border bg-surface p-6 shadow-card">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="font-display text-base font-semibold text-content">
            Fleet Summary
          </h3>
          <p className="text-sm text-content-secondary">
            {trucks.length} trucks total
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-lg bg-surface-sunken px-3 py-1 font-mono text-xs font-medium text-content-secondary">
          <span className="h-1.5 w-1.5 rounded-full bg-ok" />
          Live
        </span>
      </div>

      <div className="space-y-3">
        {STATUS_CONFIG.map(({ key, label, dot, text, bg }) => {
          const count = counts[key] ?? 0;
          const pct =
            trucks.length > 0
              ? Math.round((count / trucks.length) * 100)
              : 0;

          return (
            <div
              key={key}
              className={`flex items-center justify-between rounded-xl ${bg} px-4 py-3`}
            >
              <div className="flex items-center gap-3">
                <span className={`h-2.5 w-2.5 rounded-full ${dot}`} />
                <span className="text-sm font-medium text-slate-700">
                  {label}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/60">
                  <div
                    className={`h-full rounded-full ${dot}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className={`min-w-[1.5rem] text-right text-sm font-bold ${text}`}>
                  {count}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
