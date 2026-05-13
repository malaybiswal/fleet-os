"use client";

import React from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";

import type { Alert, DashboardSummary, Truck } from "@/types";
import { formatCurrency } from "@/lib/utils";

function KpiCard({
  label,
  value,
  change,
  changeUp,
  sparkData,
  accentColor,
  gradientId,
}: {
  label: string;
  value: string;
  change: string;
  changeUp: boolean;
  sparkData: { v: number }[];
  accentColor: string;
  gradientId: string;
}) {
  const badgeClass = changeUp
    ? "bg-emerald-50 text-emerald-700"
    : "bg-red-50 text-red-600";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${badgeClass}`}>
          {change}
        </span>
      </div>
      <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-400">Since last week</p>
      <div className="mt-4 h-12">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={sparkData}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={accentColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={accentColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="v"
              stroke={accentColor}
              strokeWidth={1.5}
              fill={`url(#${gradientId})`}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function KpiGrid({
  summary,
  trucks,
  alerts,
}: {
  summary: DashboardSummary;
  trucks: Truck[];
  alerts: Alert[];
}) {
  const activeTrucks = summary.active_trucks;
  const openAlerts = alerts.length;

  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        label="Active Trucks"
        value={String(activeTrucks)}
        change="+2"
        changeUp={true}
        accentColor="#3b82f6"
        gradientId="spark-trucks"
        sparkData={[8, 9, 7, 10, 9, 11, activeTrucks].map((v) => ({ v }))}
      />
      <KpiCard
        label="Open Alerts"
        value={String(openAlerts)}
        change="+3"
        changeUp={false}
        accentColor="#ef4444"
        gradientId="spark-alerts"
        sparkData={[3, 5, 4, 6, 5, 4, openAlerts].map((v) => ({ v }))}
      />
      <KpiCard
        label="Total Revenue"
        value={formatCurrency(summary.total_revenue)}
        change="+8%"
        changeUp={true}
        accentColor="#10b981"
        gradientId="spark-revenue"
        sparkData={[18400, 22100, 19800, 25300, 28900, 31200, Number(summary.total_revenue) || 35200].map((v) => ({ v }))}
      />
      <KpiCard
        label="Avg Rev / Mile"
        value={formatCurrency(summary.avg_revenue_per_mile)}
        change="-1%"
        changeUp={false}
        accentColor="#f59e0b"
        gradientId="spark-rpm"
        sparkData={[2.4, 2.6, 2.5, 2.3, 2.4, 2.2, Number(summary.avg_revenue_per_mile) || 2.25].map((v) => ({ v }))}
      />
    </section>
  );
}
