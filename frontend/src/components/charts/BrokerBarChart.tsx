"use client";

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
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Average Dwell by Broker
        </h2>
        <p className="text-sm text-slate-500">
          Brokers ranked by average dwell hours
        </p>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="broker" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="avgDwellHours" name="Avg Dwell Hours" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}