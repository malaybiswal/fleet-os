import React from "react";
import type { Alert } from "@/types";

export function AlertList({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Open Alerts</h3>

      <div className="mt-4 space-y-3">
        {alerts.length === 0 ? (
          <p className="text-sm text-slate-500">No open alerts.</p>
        ) : (
          alerts.slice(0, 8).map((alert) => (
            <div key={alert.id} className="rounded-xl border p-3">
              <div className="flex items-center justify-between">
                <p className="font-medium text-slate-900">{alert.alert_type}</p>
                <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
                  {alert.severity}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-500">{alert.message}</p>
              <p className="mt-2 text-xs text-slate-400">{alert.truck_id}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}