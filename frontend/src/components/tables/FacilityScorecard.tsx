"use client";

import React, { useMemo, useState } from "react";

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

type SortKey =
  | "facility_name"
  | "avg_dwell_hours"
  | "total_detention_pay"
  | "visit_count"
  | "facility_score";

export default function FacilityScorecard({ data = [] }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("facility_score");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      const aValue = sortKey === "total_detention_pay" ? Number(a.total_detention_pay) : a[sortKey];
      const bValue = sortKey === "total_detention_pay" ? Number(b.total_detention_pay) : b[sortKey];

      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortDirection === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }

      return sortDirection === "asc" ? Number(aValue) - Number(bValue) : Number(bValue) - Number(aValue);
    });
  }, [data, sortKey, sortDirection]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection(key === "facility_score" ? "asc" : "desc");
    }
  }

  function sortLabel(key: SortKey) {
    if (sortKey !== key) return "";
    return sortDirection === "asc" ? " ↑" : " ↓";
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="text-sm font-semibold text-zinc-50">Facility Scorecard</h2>
      <p className="mt-0.5 text-xs text-zinc-500">
        Facility dwell performance, detention pay, visits, and score
      </p>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-800 text-sm">
          <thead>
            <tr>
              {(
                [
                  ["facility_name", "Facility"],
                  ["avg_dwell_hours", "Avg Wait Time"],
                  ["total_detention_pay", "Detention Pay"],
                  ["visit_count", "Visits"],
                  ["facility_score", "Score"],
                ] as [SortKey, string][]
              ).map(([key, label]) => (
                <th
                  key={key}
                  onClick={() => handleSort(key)}
                  className="cursor-pointer px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  {label}{sortLabel(key)}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-zinc-800">
            {sortedData.map((row) => (
              <tr key={row.facility_name} className="hover:bg-zinc-800/50 transition-colors">
                <td className="px-4 py-3 font-medium text-zinc-200">{row.facility_name}</td>
                <td className="px-4 py-3 text-zinc-400">{row.avg_dwell_hours.toFixed(2)} hrs</td>
                <td className="px-4 py-3 text-zinc-400">${Number(row.total_detention_pay).toFixed(2)}</td>
                <td className="px-4 py-3 text-zinc-400">{row.visit_count}</td>
                <td className="px-4 py-3 font-semibold text-zinc-200">{row.facility_score.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
