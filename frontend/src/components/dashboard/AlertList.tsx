import React from "react";
import type { Alert } from "@/types";

const severityStyles: Record<string, string> = {
  critical: "bg-red-500/10 text-red-400 border border-red-500/20",
  high:     "bg-orange-500/10 text-orange-400 border border-orange-500/20",
  medium:   "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
  low:      "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20",
};

export function AlertList({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-50">Open Alerts</h3>

      <div className="mt-4 space-y-2">
        {alerts.length === 0 ? (
          <p className="text-sm text-zinc-500">No open alerts.</p>
        ) : (
          alerts.slice(0, 8).map((alert) => (
            <div key={alert.id} className="rounded-md border border-zinc-800 bg-zinc-950 p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-zinc-200">{alert.alert_type}</p>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${severityStyles[alert.severity.toLowerCase()] ?? severityStyles.low}`}>
                  {alert.severity}
                </span>
              </div>
              <p className="mt-1 text-xs text-zinc-500">{alert.message}</p>
              <p className="mt-1.5 text-xs text-zinc-600">{alert.truck_id}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
