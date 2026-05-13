"use client";

import React from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { day: "Mon", revenue: 2100, profit: 650 },
  { day: "Tue", revenue: 3200, profit: 980 },
  { day: "Wed", revenue: 2800, profit: 840 },
  { day: "Thu", revenue: 4100, profit: 1320 },
  { day: "Fri", revenue: 3600, profit: 1150 },
  { day: "Sat", revenue: 1900, profit: 500 },
  { day: "Sun", revenue: 1200, profit: 300 },
];

export function RevenueChart() {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-50">Weekly Revenue & Profit</h3>
      <p className="mt-0.5 text-xs text-zinc-500">Synthetic trend placeholder</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        <ResponsiveContainer width="100%" height={288}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="day" tick={{ fill: "#71717a", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#71717a", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "6px", color: "#fafafa" }} />
            <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="profit" stroke="#22c55e" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
