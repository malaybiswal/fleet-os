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

type BrokerScorecardRow = {
  broker_name: string;
  avg_dwell_hours: number;
  avg_loading_delay_hours: number;
  total_detention_pay: string;
  load_count: number;
};

type Props = {
  data?: BrokerScorecardRow[];
};

export default function BrokerBarChart({ data = [] }: Props) {
  const chartData = [...data]
    .sort((a, b) => b.avg_dwell_hours - a.avg_dwell_hours)
    .map((row) => ({
      broker: row.broker_name,
      avgDwellHours: Number(row.avg_dwell_hours.toFixed(2)),
    }));

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="text-sm font-semibold text-zinc-50">Average Dwell by Broker</h2>
      <p className="mt-0.5 text-xs text-zinc-500">Brokers ranked by average dwell hours</p>

      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="broker" tick={{ fill: "#71717a", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#71717a", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "6px", color: "#fafafa" }} />
            <Bar dataKey="avgDwellHours" name="Avg Dwell Hours" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
