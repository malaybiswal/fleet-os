import type { CarrierPipelineStats } from "@/types";

function KpiCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

export function CarrierKpiCards({ stats }: { stats: CarrierPipelineStats }) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        label="Total Carriers"
        value={stats.total.toLocaleString()}
        sub="In database"
      />
      <KpiCard
        label="New (Last 30 Days)"
        value={stats.new_last_30_days.toLocaleString()}
        sub="Recently added"
      />
      <KpiCard
        label="Avg Lead Score"
        value={stats.avg_lead_score != null ? stats.avg_lead_score.toFixed(1) : "—"}
        sub="Across all carriers"
      />
      <KpiCard
        label="Not Contacted"
        value={stats.not_contacted.toLocaleString()}
        sub="Need outreach"
      />
    </section>
  );
}
