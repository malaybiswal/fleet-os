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
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function LoadsTable({ loads = [] }: Props) {
  return (
    <div className="rounded-card border border-border bg-surface p-4 shadow-card">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-content">Load List</h2>
        <p className="text-sm text-content-secondary">
          Revenue, mileage, deadhead, broker, and status by load
        </p>
      </div>

      <table className="w-full table-auto divide-y divide-border text-xs">
        <thead className="bg-surface-sunken">
          <tr className="text-left text-content-secondary">
            <th className="px-2 py-2 font-semibold">Load</th>
            <th className="px-2 py-2 font-semibold">Broker</th>
            <th className="px-2 py-2 font-semibold">Route</th>
            <th className="px-2 py-2 font-semibold">Pickup</th>
            <th className="px-2 py-2 font-semibold">Delivery</th>
            <th className="px-2 py-2 text-right font-semibold">Revenue</th>
            <th className="px-2 py-2 text-right font-semibold">Miles</th>
            <th className="px-2 py-2 text-right font-semibold">RPM</th>
            <th className="px-2 py-2 text-right font-semibold">DH%</th>
            <th className="px-2 py-2 text-right font-semibold">Net Profit</th>
            <th className="px-2 py-2 font-semibold">Status</th>
            <th className="px-2 py-2 font-semibold">Facility Risk</th>
          </tr>
        </thead>

        <tbody className="divide-y divide-border">
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
              <tr key={load.id} className="transition-colors hover:bg-accent-soft">
                <td className="px-2 py-2 font-semibold text-content">
                  {load.load_id}
                </td>
                <td className="px-2 py-2 text-content-secondary">
                  {load.broker_name ?? "—"}
                </td>
                <td className="px-2 py-2 text-content-secondary">
                  <span className="font-medium">{load.origin ?? "—"}</span>
                  <span className="mx-1 text-content-muted">→</span>
                  <span className="font-medium">{load.destination ?? "—"}</span>
                </td>
                <td className="whitespace-nowrap px-2 py-2 text-content-secondary">
                  {formatDate(load.pickup_time)}
                </td>
                <td className="whitespace-nowrap px-2 py-2 text-content-secondary">
                  {formatDate(load.delivery_time)}
                </td>
                <td className="whitespace-nowrap px-2 py-2 text-right text-content-secondary">
                  {money(revenue)}
                </td>
                <td className="whitespace-nowrap px-2 py-2 text-right text-content-secondary">
                  {miles.toFixed(0)}
                </td>
                <td className="whitespace-nowrap px-2 py-2 text-right text-content-secondary">
                  ${rpm.toFixed(2)}
                </td>
                <td className="whitespace-nowrap px-2 py-2 text-right text-content-secondary">
                  {deadheadPct.toFixed(1)}%
                </td>
                <td
                  className={`whitespace-nowrap px-2 py-2 text-right font-semibold ${
                    netProfit >= 0 ? "text-emerald-700" : "text-red-700"
                  }`}
                >
                  {money(netProfit)}
                </td>
                <td className="px-2 py-2">
                  <StatusBadge status={load.status} />
                </td>
                <td className="px-2 py-2">
                  <FacilityRiskBadge facilityRisk={load.facility_risk} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
