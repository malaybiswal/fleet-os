"use client";

import React from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { facility: "Walmart DC", hours: 7.2 },
  { facility: "HEB DC",     hours: 2.1 },
  { facility: "Kroger",     hours: 4.8 },
  { facility: "Costco",     hours: 3.4 },
  { facility: "Sysco",      hours: 6.1 },
];

export function DwellChart() {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-50">Worst Facilities by Dwell Time</h3>
      <p className="mt-0.5 text-xs text-zinc-500">Synthetic trend placeholder</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        <ResponsiveContainer width="100%" height={288}>
          <BarChart data={data} layout="vertical">
            <XAxis type="number" tick={{ fill: "#71717a", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis dataKey="facility" type="category" width={90} tick={{ fill: "#71717a", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "6px", color: "#fafafa" }} />
            <Bar dataKey="hours" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
