"use client";

import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type FacilityScorecardRow = {
  facility_name: string;
  avg_dwell_hours: number;
  avg_loading_delay_hours: number;
  total_detention_pay: string;
  visit_count: number;
  facility_score: number;
};

type Props = {
  data?: FacilityScorecardRow[];
};

export default function DwellBarChart({ data = [] }: Props) {
  const chartData = [...data]
    .sort((a, b) => b.avg_dwell_hours - a.avg_dwell_hours)
    .slice(0, 10)
    .map((row) => ({
      facility: row.facility_name,
      avgDwellHours: Number(row.avg_dwell_hours.toFixed(2)),
    }));

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="text-sm font-semibold text-zinc-50">Top Worst Facilities by Dwell Time</h2>
      <p className="mt-0.5 text-xs text-zinc-500">Facilities ranked by average dwell hours</p>

      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="facility" tick={{ fill: "#71717a", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#71717a", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "6px", color: "#fafafa" }} />
            <Bar dataKey="avgDwellHours" name="Avg Dwell Hours" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
