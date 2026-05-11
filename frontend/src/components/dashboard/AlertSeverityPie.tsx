"use client";

import React from "react";
import type { Alert } from "@/types";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = ["#16a34a", "#f59e0b", "#ef4444", "#64748b"];

export function AlertSeverityPie({ alerts }: { alerts: Alert[] }) {
  const counts = alerts.reduce<Record<string, number>>((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] ?? 0) + 1;
    return acc;
  }, {});

  const data = Object.entries(counts).map(([severity, count]) => ({
    severity,
    count,
  }));

  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Alert Severity Mix</h3>
      <p className="text-sm text-slate-500">Open alerts by severity level</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            No open alerts.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="severity"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}