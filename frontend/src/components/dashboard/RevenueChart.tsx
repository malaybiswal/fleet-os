"use client";

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
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">
        Weekly Revenue & Profit
      </h3>
      <p className="text-sm text-slate-500">Synthetic trend placeholder</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        <ResponsiveContainer width="100%" height={288}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="revenue" strokeWidth={3} />
            <Line type="monotone" dataKey="profit" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}