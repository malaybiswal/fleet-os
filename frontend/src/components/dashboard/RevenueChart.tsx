"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { month: "Jan", revenue: 18400 },
  { month: "Feb", revenue: 22100 },
  { month: "Mar", revenue: 19800 },
  { month: "Apr", revenue: 25300 },
  { month: "May", revenue: 28900 },
  { month: "Jun", revenue: 24700 },
  { month: "Jul", revenue: 31200 },
  { month: "Aug", revenue: 29400 },
  { month: "Sep", revenue: 33800 },
  { month: "Oct", revenue: 30100 },
  { month: "Nov", revenue: 27600 },
  { month: "Dec", revenue: 35200 },
];

export function RevenueChart() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Revenue Activity
          </h3>
          <p className="text-sm text-slate-500">
            Showing total revenue for the last 12 months
          </p>
        </div>
        <span className="rounded-lg bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
          This Year
        </span>
      </div>

      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
          >
            <defs>
              <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#f1f5f9"
              vertical={false}
            />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                fontSize: 13,
              }}
              formatter={(value: number) => [
                `$${value.toLocaleString()}`,
                "Revenue",
              ]}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#3b82f6"
              strokeWidth={2.5}
              fill="url(#revenueGrad)"
              dot={false}
              activeDot={{ r: 5, fill: "#3b82f6", strokeWidth: 2, stroke: "#fff" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
