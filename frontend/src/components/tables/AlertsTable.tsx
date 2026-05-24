import React from "react";
import type { Alert } from "@/types";
import SeverityBadge from "@/components/ui/SeverityBadge";

type Props = {
  alerts?: Alert[];
  onResolve?: (alertId: number) => void;
};

export default function AlertsTable({ alerts = [], onResolve }: Props) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Alert List</h2>
        <p className="text-sm text-slate-500">
          Active and resolved operational alerts
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Truck
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Severity
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Type
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Message
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Status
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Created
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Action
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {alerts.map((alert) => (
              <tr key={alert.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {alert.truck_id}
                </td>
                <td className="px-4 py-3">
                  <SeverityBadge severity={alert.severity} />
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {alert.alert_type.replaceAll("_", " ")}
                </td>
                <td className="max-w-md px-4 py-3 text-slate-700">
                  {alert.message}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {alert.resolved ? "Resolved" : "Open"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {new Date(alert.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  {!alert.resolved ? (
                    <button
                      onClick={() => onResolve?.(alert.id)}
                      className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                    >
                      Resolve
                    </button>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}