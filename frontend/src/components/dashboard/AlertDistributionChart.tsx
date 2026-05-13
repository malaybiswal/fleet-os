"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Alert } from "@/types";

const SEVERITY_COLORS: Record<string, string> = {
  High: "#ef4444",
  Medium: "#f59e0b",
  Low: "#94a3b8",
};

export function AlertDistributionChart({ alerts }: { alerts: Alert[] }) {
  const data = ["high", "medium", "low"].map((sev) => {
    const label = sev.charAt(0).toUpperCase() + sev.slice(1);
    return {
      severity: label,
      count: alerts.filter((a) => a.severity === sev).length,
      color: SEVERITY_COLORS[label],
    };
  });

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm h-full">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-900">
          Alert Distribution
        </h3>
        <p className="text-sm text-slate-500">By severity level</p>
      </div>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#f1f5f9"
              vertical={false}
            />
            <XAxis
              dataKey="severity"
              tick={{ fontSize: 12, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                fontSize: 13,
              }}
              cursor={{ fill: "#f8fafc" }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
              {data.map((entry) => (
                <Cell key={entry.severity} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
