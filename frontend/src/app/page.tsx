"use client";

import { useEffect, useState } from "react";

import {
  AlertDistributionChart,
  FleetSummaryCard,
  KpiGrid,
  RevenueChart,
  TruckTable,
} from "@/components/dashboard";
import { useAuth } from "@/components/auth/AuthProvider";
import { getAlerts, getDashboardSummary, getTrucks } from "@/lib/api";
import type { Alert, DashboardSummary, Truck } from "@/types";

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function loadDashboard() {
      try {
        const [summaryData, trucksData, alertsData] = await Promise.all([
          getDashboardSummary(),
          getTrucks(),
          getAlerts(),
        ]);

        setSummary(summaryData);
        setTrucks(trucksData);
        setAlerts(alertsData);
      } catch (err) {
        console.error(err);
        setError("Failed to load dashboard data.");
      }
    }

    loadDashboard();
  }, [isAuthenticated, isLoading]);

  if (isLoading || !isAuthenticated || !summary) {
    return <p className="text-sm text-content-secondary">Loading dashboard...</p>;
  }

  if (error) {
    return <p className="text-sm text-danger">{error}</p>;
  }

  const today = new Date().toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-content">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-content-secondary">
            Fleet overview — {today}
          </p>
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