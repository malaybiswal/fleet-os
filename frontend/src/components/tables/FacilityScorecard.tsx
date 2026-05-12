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
      const aValue =
        sortKey === "total_detention_pay"
          ? Number(a.total_detention_pay)
          : a[sortKey];

      const bValue =
        sortKey === "total_detention_pay"
          ? Number(b.total_detention_pay)
          : b[sortKey];

      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortDirection === "asc"
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortDirection === "asc"
        ? Number(aValue) - Number(bValue)
        : Number(bValue) - Number(aValue);
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
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Facility Scorecard
        </h2>
        <p className="text-sm text-slate-500">
          Facility dwell performance, detention pay, visits, and score
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th
                onClick={() => handleSort("facility_name")}
                className="cursor-pointer px-4 py-3 text-left font-semibold text-slate-700"
              >
                Facility{sortLabel("facility_name")}
              </th>
              <th
                onClick={() => handleSort("avg_dwell_hours")}
                className="cursor-pointer px-4 py-3 text-left font-semibold text-slate-700"
              >
                Avg Wait Time{sortLabel("avg_dwell_hours")}
              </th>
              <th
                onClick={() => handleSort("total_detention_pay")}
                className="cursor-pointer px-4 py-3 text-left font-semibold text-slate-700"
              >
                Detention Pay{sortLabel("total_detention_pay")}
              </th>
              <th
                onClick={() => handleSort("visit_count")}
                className="cursor-pointer px-4 py-3 text-left font-semibold text-slate-700"
              >
                Visits{sortLabel("visit_count")}
              </th>
              <th
                onClick={() => handleSort("facility_score")}
                className="cursor-pointer px-4 py-3 text-left font-semibold text-slate-700"
              >
                Score{sortLabel("facility_score")}
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {sortedData.map((row) => (
              <tr key={row.facility_name} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {row.facility_name}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {row.avg_dwell_hours.toFixed(2)} hrs
                </td>
                <td className="px-4 py-3 text-slate-700">
                  ${Number(row.total_detention_pay).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {row.visit_count}
                </td>
                <td className="px-4 py-3 font-semibold text-slate-900">
                  {row.facility_score.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}