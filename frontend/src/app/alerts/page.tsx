"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import AlertsTable from "@/components/tables/AlertsTable";
import AlertFilter from "@/components/ui/AlertFilter";
import { getAlerts, resolveAlert } from "@/lib/api";

import type { Alert } from "@/types";

export default function AlertsPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function fetchAlerts() {
      try {
        const data = await getAlerts();
        setAlerts(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load alerts");
      } finally {
        setLoading(false);
      }
    }

    fetchAlerts();
  }, [isAuthenticated, isLoading]);

  const filteredAlerts =
    severityFilter === "all"
      ? alerts
      : alerts.filter((alert) => alert.severity === severityFilter);

  async function handleResolve(alertId: number) {
    const previousAlerts = alerts;

    setAlerts((currentAlerts) =>
      currentAlerts.map((alert) =>
        alert.id === alertId ? { ...alert, resolved: true } : alert,
      ),
    );

    try {
      await resolveAlert(alertId);
    } catch (err) {
      console.error(err);
      setAlerts(previousAlerts);
      setError("Failed to resolve alert");
    }
  }

  if (isLoading || loading) {
    return <div className="p-6">Loading alerts...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <main className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold">Alerts</h1>
        <p className="text-gray-500">
          Monitor fleet alerts, severity, and resolution status
        </p>
      </div>

      <AlertFilter value={severityFilter} onChange={setSeverityFilter} />

      <AlertsTable alerts={filteredAlerts} onResolve={handleResolve} />
    </main>
  );
}