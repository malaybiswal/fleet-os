"use client";

import React from "react";
import type { Truck } from "@/types";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = ["#16a34a", "#f59e0b", "#2563eb", "#64748b", "#ef4444"];

export function TruckStatusPie({ trucks }: { trucks: Truck[] }) {
  const counts = trucks.reduce<Record<string, number>>((acc, truck) => {
    acc[truck.status] = (acc[truck.status] ?? 0) + 1;
    return acc;
  }, {});

  const data = Object.entries(counts).map(([status, count]) => ({
    status,
    count,
  }));

  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Truck Status Mix</h3>
      <p className="text-sm text-slate-500">Moving, slow, idle, stopped, and maintenance split</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            No truck data available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="status"
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
