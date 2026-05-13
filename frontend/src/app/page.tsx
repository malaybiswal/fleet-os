import {
  AlertDistributionChart,
  FleetSummaryCard,
  KpiGrid,
  RevenueChart,
  TruckTable,
} from "@/components/dashboard";
import { getAlerts, getDashboardSummary, getTrucks } from "@/lib/api";

export default async function DashboardPage() {
  const [summary, trucks, alerts] = await Promise.all([
    getDashboardSummary(),
    getTrucks(),
    getAlerts(),
  ]);

  const today = new Date().toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Fleet overview — {today}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50">
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
            Pick a date
          </button>
          <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
            + Export
          </button>
        </div>
      </div>

      <KpiGrid summary={summary} trucks={trucks} alerts={alerts} />

      <RevenueChart />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TruckTable trucks={trucks} />
        </div>
        <AlertDistributionChart alerts={alerts} />
      </div>

      <FleetSummaryCard trucks={trucks} />
    </div>
  );
}
