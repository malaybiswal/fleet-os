"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { CarrierKpiCards } from "@/components/carriers/CarrierKpiCards";
import { DemoCarrierCard } from "@/components/carriers/DemoCarrierCard";
import { OutreachBoard } from "@/components/carriers/OutreachBoard";
import {
  getCarrierPipelineStats,
  listCarriers,
  listNewCarriers,
} from "@/lib/api";
import type { CarrierListItem, CarrierPipelineStats } from "@/types";
import {
  GROWTH_FLEET_MAX_UNITS,
  GROWTH_FLEET_MIN_UNITS,
} from "@/components/carriers/demoSignals";

type Segment = "new" | "growth" | "top" | "pipeline";

const SEGMENTS: { key: Segment; label: string; description: string }[] = [
  {
    key: "top",
    label: "Top Prospects",
    description: "Highest-scoring carriers across our pipeline",
  },
  {
    key: "new",
    label: "New Authorities",
    description: "Carriers that recently received operating authority",
  },
  {
    key: "growth",
    label: "Growth Fleets",
    description: `Carriers with ${GROWTH_FLEET_MIN_UNITS}-${GROWTH_FLEET_MAX_UNITS} trucks — the sweet spot for adoption`,
  },
  {
    key: "pipeline",
    label: "Pipeline",
    description: "Drag carriers across outreach stages to work your pipeline",
  },
];

export default function CarrierDemoPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [stats, setStats] = useState<CarrierPipelineStats | null>(null);
  const [segment, setSegment] = useState<Segment>("top");
  const [carriers, setCarriers] = useState<CarrierListItem[]>([]);
  const [loadingCarriers, setLoadingCarriers] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    getCarrierPipelineStats().then(setStats);
  }, [isAuthenticated, isLoading]);

  useEffect(() => {
    if (isLoading || !isAuthenticated || segment === "pipeline") return;
    setLoadingCarriers(true);
    setError(null);

    const promise =
      segment === "new"
        ? listNewCarriers()
        : segment === "growth"
          ? listCarriers({
              power_units_min: GROWTH_FLEET_MIN_UNITS,
              power_units_max: GROWTH_FLEET_MAX_UNITS,
              order_by: "lead_score_desc",
              page_size: 12,
            })
          : listCarriers({ order_by: "lead_score_desc", page_size: 12 });

    promise
      .then((result) => setCarriers(result.data))
      .catch(() => setError("Failed to load carriers"))
      .finally(() => setLoadingCarriers(false));
  }, [isAuthenticated, isLoading, segment]);

  if (isLoading) {
    return <div className="p-6 text-slate-500">Loading…</div>;
  }

  const active = SEGMENTS.find((s) => s.key === segment) ?? SEGMENTS[0];

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-slate-900">Carrier Prospects</h1>
            <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
              Demo
            </span>
          </div>
          <p className="text-slate-500">
            High-potential carriers, ranked and ready for outreach
          </p>
        </div>
        <Link
          href="/carriers"
          className="whitespace-nowrap rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-500 hover:bg-slate-50"
        >
          Full Carrier Database →
        </Link>
      </div>

      {stats && <CarrierKpiCards stats={stats} />}

      <div className="flex flex-wrap gap-2">
        {SEGMENTS.map((s) => (
          <button
            key={s.key}
            onClick={() => setSegment(s.key)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              segment === s.key
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-600 hover:bg-slate-100"
            } border border-slate-200`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <p className="text-sm text-slate-500">{active.description}</p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {segment === "pipeline" && <OutreachBoard />}

      {segment !== "pipeline" && loadingCarriers && (
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-400 shadow-sm">
          Loading prospects…
        </div>
      )}

      {segment !== "pipeline" && !loadingCarriers && carriers.length === 0 && !error && (
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-400 shadow-sm">
          No carriers found in this segment.
        </div>
      )}

      {segment !== "pipeline" && !loadingCarriers && carriers.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {carriers.map((c) => (
            <DemoCarrierCard key={c.id} carrier={c} />
          ))}
        </div>
      )}
    </div>
  );
}
