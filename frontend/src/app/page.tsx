import {
  AlertList,
  AlertSeverityPie,
  DwellChart,
  KpiGrid,
  OperationsMap,
  RevenueChart,
  TruckStatusPie,
  TruckTable,
} from "@/components/dashboard";
import { getAlerts, getDashboardSummary, getTrucks } from "@/lib/api";

export default async function DashboardPage() {
  const [summary, trucks, alerts] = await Promise.all([
    getDashboardSummary(),
    getTrucks(),
    getAlerts(),
  ]);

  return (
  <div className="space-y-6">
    <KpiGrid summary={summary} />

    <section className="grid gap-6 lg:grid-cols-2">
      <TruckStatusPie trucks={trucks} />
      <AlertSeverityPie alerts={alerts} />
    </section>

    <section className="grid gap-6 lg:grid-cols-2">
      <RevenueChart />
      <DwellChart />
    </section>

    <section className="grid gap-6 lg:grid-cols-2">
      <TruckTable trucks={trucks} />
      <AlertList alerts={alerts} />
    </section>

    <OperationsMap trucks={trucks} />
  </div>
);
}