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
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Top Worst Facilities by Dwell Time
        </h2>
        <p className="text-sm text-slate-500">
          Facilities ranked by average dwell hours
        </p>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="facility" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="avgDwellHours" name="Avg Dwell Hours" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}