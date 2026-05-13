"use client";

import { useEffect, useState } from "react";

import AlertFilter from "@/components/ui/AlertFilter";
import AlertsTable from "@/components/tables/AlertsTable";

export type Alert = {
  id: number;
  truck_id: string;
  severity: "low" | "medium" | "high" | string;
  alert_type: string;
  message: string;
  resolved: boolean;
  created_at: string;
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchAlerts() {
      try {
        const response = await fetch("http://localhost:8000/api/alerts");

        if (!response.ok) {
          throw new Error("Failed to fetch alerts");
        }

        const data = await response.json();
        setAlerts(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load alerts");
      } finally {
        setLoading(false);
      }
    }

    fetchAlerts();
  }, []);

  const filteredAlerts =
    severityFilter === "all"
      ? alerts
      : alerts.filter((alert) => alert.severity === severityFilter);

  async function handleResolve(alertId: number) {
    const previousAlerts = alerts;

    setAlerts((currentAlerts) =>
      currentAlerts.map((alert) =>
        alert.id === alertId ? { ...alert, resolved: true } : alert
      )
    );

    try {
      const response = await fetch(
        `http://localhost:8000/api/alerts/${alertId}/resolve`,
        { method: "PATCH" }
      );

      if (!response.ok) {
        throw new Error("Failed to resolve alert");
      }
    } catch (err) {
      console.error(err);
      setAlerts(previousAlerts);
      setError("Failed to resolve alert");
    }
  }

  if (loading) {
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