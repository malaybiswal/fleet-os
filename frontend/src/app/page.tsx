import { getAlerts, getDashboardSummary, getTrucks } from "@/lib/api";
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

export default async function DashboardPage() {
  const [summary, trucks, alerts] = await Promise.all([
    getDashboardSummary(),
    getTrucks(),
    getAlerts(),
  ]);

  return (
    <div className="space-y-6">
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
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Truck Status</h3>
          <div className="mt-4 space-y-3">
            {trucks.length === 0 ? (
              <p className="text-sm text-slate-500">No trucks available.</p>
            ) : (
              trucks.slice(0, 5).map((truck) => (
                <div
                  key={truck.truck_id}
                  className="flex items-center justify-between rounded-xl border p-3"
                >
                  <div>
                    <p className="font-medium text-slate-900">{truck.truck_id}</p>
                    <p className="text-sm text-slate-500">
                      {truck.current_location ?? "Unknown location"}
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {truck.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Open Alerts</h3>
          <div className="mt-4 space-y-3">
            {alerts.length === 0 ? (
              <p className="text-sm text-slate-500">No open alerts.</p>
            ) : (
              alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="rounded-xl border p-3">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-slate-900">
                      {alert.alert_type}
                    </p>
                    <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
                      {alert.severity}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">{alert.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}