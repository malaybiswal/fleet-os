import React from "react";

import type { DashboardSummary } from "@/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

function KpiCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper?: string;
}) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      {helper ? <p className="mt-1 text-xs text-slate-400">{helper}</p> : null}
    </div>
  );
}

export function KpiGrid({ summary }: { summary: DashboardSummary }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <KpiCard label="Active Trucks" value={String(summary.active_trucks)} />
      <KpiCard
        label="Avg Dwell Time"
        value={`${formatNumber(summary.avg_dwell_hours)}h`}
        helper="Target: under 3h"
      />
      <KpiCard
        label="Revenue / Mile"
        value={formatCurrency(Number(summary.avg_revenue_per_mile))}
      />
      <KpiCard label="Open Alerts" value={String(summary.open_alerts)} />
      <KpiCard label="Open Loads" value={String(summary.open_loads)} />
      <KpiCard
        label="Fuel Cost / Mile"
        value={formatCurrency(Number(summary.fuel_cost_per_mile))}
      />
      <KpiCard
        label="Deadhead %"
        value={`${formatNumber(summary.deadhead_percentage)}%`}
      />
      <KpiCard
        label="Total Revenue"
        value={formatCurrency(Number(summary.total_revenue))}
      />
    </section>
  );
}