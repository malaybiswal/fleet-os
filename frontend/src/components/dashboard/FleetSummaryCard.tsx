import type { Truck } from "@/types";

const STATUS_CONFIG = [
  {
    key: "active",
    label: "Active",
    dot: "bg-emerald-500",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
  },
  {
    key: "idle",
    label: "Idle",
    dot: "bg-amber-500",
    text: "text-amber-700",
    bg: "bg-amber-50",
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
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Fleet Summary
          </h3>
          <p className="text-sm text-slate-500">{trucks.length} trucks total</p>
        </div>
        <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
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
