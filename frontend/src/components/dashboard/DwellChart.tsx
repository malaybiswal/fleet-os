"use client";

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
  { facility: "HEB DC", hours: 2.1 },
  { facility: "Kroger", hours: 4.8 },
  { facility: "Costco", hours: 3.4 },
  { facility: "Sysco", hours: 6.1 },
];

export function DwellChart() {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">
        Worst Facilities by Dwell Time
      </h3>
      <p className="text-sm text-slate-500">Synthetic trend placeholder</p>

      <div className="mt-4" style={{ width: "100%", height: 288 }}>
        <ResponsiveContainer width="100%" height={288}>
          <BarChart data={data} layout="vertical">
            <XAxis type="number" />
            <YAxis dataKey="facility" type="category" width={90} />
            <Tooltip />
            <Bar dataKey="hours" radius={[0, 8, 8, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}