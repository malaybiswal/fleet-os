"use client";

import { useRouter } from "next/navigation";

import { formatPhone } from "@/lib/utils";
import type { CarrierListItem } from "@/types";
import {
  formatFleetSize,
  isGrowthFleet,
  isNewAuthority,
  prospectTier,
} from "./demoSignals";

const TIER_STYLES: Record<string, string> = {
  hot: "bg-emerald-100 text-emerald-700",
  warm: "bg-amber-100 text-amber-700",
  cold: "bg-slate-100 text-slate-500",
};

const TIER_LABELS: Record<string, string> = {
  hot: "Hot Prospect",
  warm: "Warm Prospect",
  cold: "Prospect",
};

export function DemoCarrierCard({ carrier }: { carrier: CarrierListItem }) {
  const router = useRouter();
  const tier = prospectTier(carrier);

  return (
    <div
      role="link"
      tabIndex={0}
      onClick={() => router.push(`/carriers/${carrier.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter") router.push(`/carriers/${carrier.id}`);
      }}
      className="cursor-pointer rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{carrier.legal_name}</h3>
          {carrier.dba_name && (
            <p className="text-sm text-slate-400">DBA: {carrier.dba_name}</p>
          )}
          <p className="mt-1 text-sm text-slate-500">
            {[carrier.city, carrier.state].filter(Boolean).join(", ") || "Location unknown"}
          </p>
        </div>
        <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${TIER_STYLES[tier]}`}>
          {TIER_LABELS[tier]}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
        <span className="rounded-md bg-slate-50 px-2.5 py-1 font-medium text-slate-700">
          {formatFleetSize(carrier.power_units)}
        </span>
        {isNewAuthority(carrier) && (
          <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-semibold text-blue-700">
            New Authority
          </span>
        )}
        {isGrowthFleet(carrier) && (
          <span className="rounded-full bg-purple-100 px-2.5 py-1 text-xs font-semibold text-purple-700">
            Growing
          </span>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-slate-500">
          {carrier.cargo_types?.[0]
            ? carrier.cargo_types[0].replaceAll("_", " ")
            : "General freight"}
        </span>
        {carrier.phone ? (
          <a
            href={`tel:${carrier.phone}`}
            onClick={(e) => e.stopPropagation()}
            className="font-medium text-blue-600 hover:underline"
          >
            {formatPhone(carrier.phone)}
          </a>
        ) : (
          <span className="text-slate-400">No phone on file</span>
        )}
      </div>
    </div>
  );
}
