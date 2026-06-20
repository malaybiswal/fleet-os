import React from "react";

import FacilityRiskBadge from "@/components/ui/FacilityRiskBadge";
import StatusBadge from "@/components/ui/StatusBadge";
import type { Load } from "@/types";

export type { Load };

type Props = {
  loads?: Load[];
};

function money(value?: string | number | null) {
  return `$${Number(value ?? 0).toFixed(2)}`;
}

function num(value?: string | number | null) {
  return Number(value ?? 0);
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export default function LoadsTable({ loads = [] }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Load List</h2>
        <p className="text-sm text-slate-500">
          Revenue, mileage, deadhead, broker, and status by load
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[1400px] divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Load</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Broker</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Route</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Pickup</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Delivery</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Revenue</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Miles</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">RPM</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Deadhead %</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Net Profit</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Status</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Facility Risk</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {loads.map((load) => {
              const revenue = num(load.revenue);
              const miles = num(load.miles);
              const deadheadMiles = num(load.deadhead_miles);
              const totalCost =
                num(load.fuel_cost) +
                num(load.maintenance_reserve) +
                num(load.driver_cost) +
                num(load.tolls);

              const rpm = miles > 0 ? revenue / miles : 0;
              const deadheadPct = miles > 0 ? (deadheadMiles / miles) * 100 : 0;
              const netProfit = revenue - totalCost;

              return (
                <tr key={load.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 font-semibold text-slate-900">
                    {load.load_id}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    {load.broker_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    <span className="font-medium">{load.origin ?? "—"}</span>
                    <span className="mx-2 text-slate-400">→</span>
                    <span className="font-medium">{load.destination ?? "—"}</span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    {formatDate(load.pickup_time)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    {formatDate(load.delivery_time)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    {money(revenue)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    {miles.toFixed(0)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    ${rpm.toFixed(2)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                    {deadheadPct.toFixed(1)}%
                  </td>
                  <td
                    className={`whitespace-nowrap px-4 py-3 font-semibold ${
                      netProfit >= 0 ? "text-green-700" : "text-red-700"
                    }`}
                  >
                    {money(netProfit)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <StatusBadge status={load.status} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <FacilityRiskBadge facilityRisk={load.facility_risk} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
