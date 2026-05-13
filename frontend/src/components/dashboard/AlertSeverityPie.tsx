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

const COLORS = ["#22c55e", "#f59e0b", "#ef4444", "#6b7280"];

export function AlertSeverityPie({ alerts }: { alerts: Alert[] }) {
  const counts = alerts.reduce<Record<string, number>>((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] ?? 0) + 1;
    return acc;
  }, {});

  const data = Object.entries(counts).map(([severity, count]) => ({ severity, count }));

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-50">Alert Severity Mix</h3>
      <p className="mt-0.5 text-xs text-zinc-500">Open alerts by severity level</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-zinc-500">
            No open alerts.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <PieChart>
              <Pie data={data} dataKey="count" nameKey="severity" cx="50%" cy="50%" outerRadius={90} label>
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "6px", color: "#fafafa" }} />
              <Legend wrapperStyle={{ color: "#a1a1aa", fontSize: "12px" }} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
