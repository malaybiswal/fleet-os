"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import StatusBadge from "@/components/ui/StatusBadge";
import SeverityBadge from "@/components/ui/SeverityBadge";
import FacilityRiskBadge from "@/components/ui/FacilityRiskBadge";
import {
  acceptDispatcherRecommendation,
  getDispatcherCandidates,
  getDispatcherDecision,
} from "@/lib/api";
import type {
  DispatcherCommandCenterDecision,
  DispatcherDecisionMetrics,
  DispatcherRecommendation,
  DispatcherTruckOption,
  Load,
} from "@/types";

const recommendationStyles: Record<DispatcherRecommendation, string> = {
  RECOMMENDED: "border-green-200 bg-green-50 text-green-900",
  REVIEW: "border-amber-200 bg-amber-50 text-amber-900",
  AVOID: "border-red-200 bg-red-50 text-red-900",
};

const recommendationLabels: Record<DispatcherRecommendation, string> = {
  RECOMMENDED: "RECOMMENDED",
  REVIEW: "REVIEW",
  AVOID: "AVOID",
};

const brokerRiskStyles: Record<string, string> = {
  low: "border-green-200 bg-green-50 text-green-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  high: "border-red-200 bg-red-50 text-red-700",
};

const demoShowcaseLoadOrder = [
  "DEMO-CAND-GOOD",
  "DEMO-CAND-WEAK-BROKER",
  "DEMO-CAND-BAD-DEADHEAD",
];

export default function DispatcherCommandCenterPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [loads, setLoads] = useState<Load[]>([]);
  const [loadsLoading, setLoadsLoading] = useState(true);
  const [selectedLoadId, setSelectedLoadId] = useState<string | null>(null);
  const [decision, setDecision] =
    useState<DispatcherCommandCenterDecision | null>(null);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [acceptLoading, setAcceptLoading] = useState(false);
  const [assignmentMessage, setAssignmentMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function loadData() {
      try {
        setLoadsLoading(true);
        setError(null);
        setLoads(await getDispatcherCandidates());
      } catch (err) {
        console.error(err);
        setError(readableApiError(err, "Failed to load candidate loads."));
      } finally {
        setLoadsLoading(false);
      }
    }

    loadData();
  }, [isAuthenticated, isLoading]);

  async function selectLoad(loadId: string) {
    setSelectedLoadId(loadId);
    setDecision(null);
    setDecisionLoading(true);
    setAssignmentMessage(null);
    setError(null);

    try {
      setDecision(await getDispatcherDecision(loadId));
    } catch (err) {
      console.error(err);
      setError(readableApiError(err, "Failed to load dispatcher decision."));
    } finally {
      setDecisionLoading(false);
    }
  }

  async function acceptRecommendation() {
    if (!selectedLoadId || !decision?.best_truck || !decision.is_candidate) {
      return;
    }

    setAcceptLoading(true);
    setError(null);
    setAssignmentMessage(null);

    try {
      const assignedLoad = await acceptDispatcherRecommendation(
        selectedLoadId,
        decision.best_truck.truck_id,
        decision.best_truck.driver_id,
      );
      setLoads(await getDispatcherCandidates());
      setSelectedLoadId(null);
      setDecision(null);
      setAssignmentMessage(
        `Booked ${assignedLoad.load_id} to ${assignedLoad.truck_id ?? "selected truck"} with ${assignedLoad.driver_id ?? "selected driver"}.`,
      );
    } catch (err) {
      console.error(err);
      setError(readableApiError(err, "Failed to accept recommendation."));
    } finally {
      setAcceptLoading(false);
    }
  }

  if (isLoading || !isAuthenticated || loadsLoading) {
    return <p className="text-sm text-slate-500">Loading command center...</p>;
  }

  const commandCenterLoads = commandCenterLoadList(loads);
  const selectedLoad =
    commandCenterLoads.find((load) => load.load_id === selectedLoadId) ?? null;

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Dispatcher Command Center
        </h1>
        <p className="mt-0.5 text-sm text-slate-500">
          Select a load and review FleetOS truck assignment guidance.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {assignmentMessage && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {assignmentMessage}
        </div>
      )}

      <div className="grid gap-6 2xl:grid-cols-[minmax(360px,0.8fr)_minmax(0,1.45fr)]">
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <h2 className="text-base font-semibold text-slate-900">Fleet Loads</h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Choose a candidate load for dispatch evaluation.
            </p>
          </div>

          {commandCenterLoads.length === 0 ? (
            <div className="px-4 py-8 text-sm text-slate-500">
              No loads are available for command-center evaluation.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {commandCenterLoads.map((load) => (
                <button
                  key={load.load_id}
                  type="button"
                  aria-pressed={selectedLoadId === load.load_id}
                  onClick={() => selectLoad(load.load_id)}
                  className={`w-full px-4 py-4 text-left transition ${
                    selectedLoadId === load.load_id
                      ? "bg-blue-50"
                      : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold text-slate-900">
                        {load.load_id}
                      </div>
                      <div className="mt-1 text-sm text-slate-600">
                        {load.origin ?? "Unknown origin"} to{" "}
                        {load.destination ?? "Unknown destination"}
                      </div>
                    </div>
                    <StatusBadge status={load.status} />
                  </div>

                  <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
                    <span>Broker: {load.broker_name ?? "-"}</span>
                    <span>Revenue: {money(load.revenue)}</span>
                    <span>Miles: {number(load.miles).toFixed(0)}</span>
                    <span>
                      Deadhead: {number(load.deadhead_miles).toFixed(0)} mi
                    </span>
                  </div>

                  <div className="mt-3">
                    <FacilityRiskBadge facilityRisk={load.facility_risk} />
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <h2 className="text-base font-semibold text-slate-900">
              Dispatch Decision
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Truck recommendation, economics, facility risk, and ranking reasons.
            </p>
          </div>

          <div className="p-4">
            {decisionLoading ? (
              <div className="rounded-lg bg-slate-50 px-4 py-8 text-sm text-slate-500">
                Loading dispatcher decision...
              </div>
            ) : !selectedLoad ? (
              <div className="rounded-lg bg-slate-50 px-4 py-8 text-sm text-slate-500">
                Select a load to see the recommended truck assignment.
              </div>
            ) : !decision ? (
              <div className="rounded-lg bg-slate-50 px-4 py-8 text-sm text-slate-500">
                No decision is loaded for {selectedLoad.load_id}.
              </div>
            ) : (
              <DecisionPanel
                decision={decision}
                onAccept={acceptRecommendation}
                acceptLoading={acceptLoading}
              />
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function DecisionPanel({
  decision,
  onAccept,
  acceptLoading,
}: {
  decision: DispatcherCommandCenterDecision;
  onAccept: () => void;
  acceptLoading: boolean;
}) {
  const style = recommendationStyles[decision.final_recommendation];
  const canAccept = Boolean(decision.best_truck && decision.is_candidate);
  const [selectedTruckOption, setSelectedTruckOption] =
    useState<DispatcherTruckOption | null>(null);

  return (
    <div className="space-y-5">
      <div className={`rounded-lg border px-5 py-4 ${style}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide opacity-80">
              FleetOS Recommendation
            </div>
            <div className="mt-1 text-3xl font-bold">
              {recommendationLabels[decision.final_recommendation]}
            </div>
            <div className="mt-2 text-sm">
              {decision.best_truck
                ? `Best truck: ${decision.best_truck.truck_id} with ${decision.best_truck.driver_name}`
                : "No eligible truck is available for this load."}
            </div>
          </div>

          <button
            type="button"
            onClick={onAccept}
            disabled={!canAccept || acceptLoading}
            className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600"
          >
            {acceptLoading ? "Accepting..." : "Accept recommendation"}
          </button>
        </div>
      </div>

      <SelectedLoadSummary
        load={decision.load}
        brokerRiskBand={decision.metrics.broker_risk_band}
      />

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <Metric
          label="Revenue / Hour"
          value={money(decision.metrics.estimated_revenue_per_hour)}
        />
        <Metric
          label="Deadhead"
          value={`${decision.metrics.deadhead_miles.toFixed(0)} mi`}
        />
        <Metric
          label="Profitability Score"
          value={`${decision.metrics.profitability_score.toFixed(0)}/100`}
        />
        <Metric
          label="Net Margin"
          value={money(decision.metrics.net_margin)}
        />
        <Metric
          label="Final Dispatch Score"
          value={
            decision.metrics.final_dispatch_score === null
              ? "-"
              : `${decision.metrics.final_dispatch_score.toFixed(0)}/100`
          }
        />
      </div>

      <ScoreBreakdown metrics={decision.metrics} />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-semibold text-slate-900">
            Facility Risk
          </h3>
          <div className="mt-3">
            <FacilityRiskBadge facilityRisk={decision.facility_risk} />
          </div>
          {decision.facility_risk && (
            <p className="mt-3 text-sm text-slate-600">
              {decision.facility_risk.facility_name}
            </p>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-semibold text-slate-900">
            Decision Reasons
          </h3>
          <ul className="mt-3 space-y-2">
            {decision.reasons.map((reason) => (
              <li key={reason} className="text-sm text-slate-700">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              Ranked Truck Options
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Click a truck row to inspect HOS, alerts, economics, and ranking factors.
            </p>
          </div>
        </div>
        {decision.truck_options.length === 0 ? (
          <p className="mt-3 rounded-lg bg-slate-50 px-4 py-5 text-sm text-slate-500">
            No eligible truck options were returned.
          </p>
        ) : (
          <div className="mt-3 overflow-x-auto rounded-lg border border-slate-200">
            <table className="min-w-[620px] table-fixed divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="w-10 px-2 py-2 text-left font-semibold text-slate-700">
                    Rank
                  </th>
                  <th className="w-24 px-2 py-2 text-left font-semibold text-slate-700">
                    Truck
                  </th>
                  <th className="w-28 px-2 py-2 text-left font-semibold text-slate-700">
                    Driver
                  </th>
                  <th className="w-24 px-2 py-2 text-left font-semibold text-slate-700">
                    Status
                  </th>
                  <th className="w-36 px-2 py-2 text-left font-semibold text-slate-700">
                    Location
                  </th>
                  <th className="w-24 px-2 py-2 text-left font-semibold text-slate-700">
                    Pickup
                  </th>
                  <th className="w-16 px-2 py-2 text-left font-semibold text-slate-700">
                    Score
                  </th>
                  <th className="w-20 px-2 py-2 text-left font-semibold text-slate-700">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {decision.truck_options.map((option, index) => (
                  <TruckOptionRow
                    key={option.truck_id}
                    option={option}
                    rank={index + 1}
                    onInspect={setSelectedTruckOption}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedTruckOption && (
        <TruckOptionDetailsPanel
          option={selectedTruckOption}
          onClose={() => setSelectedTruckOption(null)}
        />
      )}

      {decision.decision_notes.length > 0 && (
        <div className="rounded-lg bg-slate-50 px-4 py-3 text-xs text-slate-500">
          {decision.decision_notes.map((note) => (
            <p key={note}>{note}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function ScoreBreakdown({ metrics }: { metrics: DispatcherDecisionMetrics }) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <h3 className="text-sm font-semibold text-slate-900">Score Breakdown</h3>
      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2 lg:grid-cols-6">
        <span>Profitability baseline: {nullableNumber(metrics.profitability_baseline)}</span>
        <span>Facility multiplier: {nullableNumber(metrics.facility_multiplier, 2)}</span>
        <span>Broker multiplier: {nullableNumber(metrics.broker_multiplier, 2)}</span>
        <span>Alert penalty: {nullableNumber(metrics.alert_penalty)}</span>
        <span>Strategy bonus: {nullableNumber(metrics.strategy_bonus)}</span>
        <span>Final dispatch: {nullableNumber(metrics.final_dispatch_score)}</span>
      </div>
    </div>
  );
}

function SelectedLoadSummary({
  load,
  brokerRiskBand,
}: {
  load: Load;
  brokerRiskBand: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Selected Load</h3>
          <p className="mt-1 text-sm text-slate-600">
            {load.origin ?? "Unknown origin"} to{" "}
            {load.destination ?? "Unknown destination"}
          </p>
        </div>
        <StatusBadge status={load.status} />
      </div>

      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2 xl:grid-cols-4">
        <span className="flex items-center gap-2">
          <span>Broker: {load.broker_name ?? "-"}</span>
          <BrokerRiskBadge band={brokerRiskBand} />
        </span>
        <span>Revenue: {money(load.revenue)}</span>
        <span>Miles: {number(load.miles).toFixed(0)}</span>
        <span>Deadhead: {number(load.deadhead_miles).toFixed(0)} mi</span>
      </div>
    </div>
  );
}

function BrokerRiskBadge({ band }: { band: string }) {
  const normalized = band.toLowerCase();
  const style = brokerRiskStyles[normalized] ?? brokerRiskStyles.medium;

  return (
    <span
      className={`whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium ${style}`}
    >
      {normalized.toUpperCase()} broker risk
    </span>
  );
}

function TruckOptionRow({
  option,
  rank,
  onInspect,
}: {
  option: DispatcherTruckOption;
  rank: number;
  onInspect: (option: DispatcherTruckOption) => void;
}) {
  return (
    <tr
      tabIndex={0}
      onClick={() => onInspect(option)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onInspect(option);
        }
      }}
      className="cursor-pointer transition hover:bg-blue-50 focus:bg-blue-50 focus:outline-none"
      aria-label={`View details for ${option.truck_id}`}
    >
      <td className="whitespace-nowrap px-2 py-3 font-semibold text-slate-900">
        {rank}
      </td>
      <td className="whitespace-nowrap px-2 py-3 font-semibold text-slate-900">
        {option.truck_id}
      </td>
      <td className="px-2 py-3 text-slate-700">
        <div className="truncate font-medium text-slate-900">{option.driver_name}</div>
        <div className="truncate text-[11px] text-slate-500">{option.driver_id}</div>
      </td>
      <td className="whitespace-nowrap px-2 py-3">
        <StatusBadge status={option.status} />
      </td>
      <td className="px-2 py-3 text-slate-700">
        <div className="truncate" title={option.current_location ?? "-"}>
          {option.current_location ?? "-"}
        </div>
      </td>
      <td className="whitespace-nowrap px-2 py-3">
        <span
          className={`rounded-full px-1.5 py-1 text-[11px] font-medium ${
            option.can_make_pickup
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {option.can_make_pickup ? "Makes pickup" : "Misses pickup"}
        </span>
      </td>
      <td className="whitespace-nowrap px-2 py-3 text-slate-700">
        {option.rank_score.toFixed(0)}
      </td>
      <td className="px-2 py-3 text-blue-700">
        View details
      </td>
    </tr>
  );
}

function TruckOptionDetailsPanel({
  option,
  onClose,
}: {
  option: DispatcherTruckOption;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/30" onClick={onClose}>
      <aside
        className="h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        aria-label={`Truck details for ${option.truck_id}`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Ranked truck option
            </p>
            <h3 className="mt-1 text-xl font-bold text-slate-900">
              {option.truck_id}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              {option.driver_name} · {option.driver_id}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Close
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <DetailMetric label="Dispatch score" value={`${option.rank_score.toFixed(0)}/100`} />
          <DetailMetric label="Recommendation" value={recommendationLabels[option.recommendation]} />
          <DetailMetric
            label="HOS remaining"
            value={
              option.driver_hos_hours_remaining === null
                ? "-"
                : `${option.driver_hos_hours_remaining.toFixed(1)}h`
            }
          />
          <DetailMetric label="Status" value={option.status.replaceAll("_", " ")} />
          <DetailMetric label="Location" value={option.current_location ?? "-"} />
          <DetailMetric
            label="Last seen"
            value={option.last_seen_at ? new Date(option.last_seen_at).toLocaleString() : "-"}
          />
          <DetailMetric label="Deadhead" value={`${option.deadhead_miles.toFixed(0)} mi`} />
          <DetailMetric label="Deadhead source" value={option.deadhead_source} />
          <DetailMetric
            label="Pickup feasibility"
            value={option.can_make_pickup ? "Can make pickup" : "Misses pickup"}
          />
          <DetailMetric label="Active alerts" value={`${option.active_alert_count}`} />
          <DetailMetric
            label="Highest alert severity"
            value={option.highest_alert_severity ?? "None"}
          />
          <DetailMetric
            label="Revenue / hour"
            value={money(option.estimated_revenue_per_hour)}
          />
          <DetailMetric
            label="Profitability score"
            value={`${option.profitability_score.toFixed(0)}/100`}
          />
          <DetailMetric
            label="Operational score"
            value={`${option.operational_score.toFixed(0)}/100`}
          />
        </div>

        <div className="mt-5 rounded-lg border border-slate-200 p-4">
          <h4 className="text-sm font-semibold text-slate-900">Score breakdown</h4>
          <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
            <span>Profitability baseline: {nullableNumber(option.score_breakdown.profitability_baseline)}</span>
            <span>Facility multiplier: {nullableNumber(option.score_breakdown.facility_multiplier, 2)}</span>
            <span>Broker multiplier: {nullableNumber(option.score_breakdown.broker_multiplier, 2)}</span>
            <span>Alert penalty: {nullableNumber(option.score_breakdown.alert_penalty)}</span>
            <span>Strategy bonus: {nullableNumber(option.score_breakdown.strategy_bonus)}</span>
            <span>Final dispatch: {nullableNumber(option.score_breakdown.final_dispatch_score)}</span>
          </div>
        </div>

        <div className="mt-5 rounded-lg border border-slate-200 p-4">
          <h4 className="text-sm font-semibold text-slate-900">Ranking factors</h4>
          {option.ranking_factors.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No ranking factors were returned.</p>
          ) : (
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
              {option.ranking_factors.map((factor) => (
                <li key={factor}>{factor}</li>
              ))}
            </ul>
          )}
        </div>

        {option.reasons.length > 0 && (
          <div className="mt-5 rounded-lg border border-slate-200 p-4">
            <h4 className="text-sm font-semibold text-slate-900">Decision reasons</h4>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
              {option.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </div>
  );
}

function DetailMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 px-3 py-2">
      <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 px-4 py-3">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-bold text-slate-900">{value}</div>
    </div>
  );
}

function money(value?: string | number | null) {
  return `$${number(value).toFixed(2)}`;
}

function nullableNumber(value?: number | null, digits = 0) {
  return value === null || value === undefined ? "-" : value.toFixed(digits);
}

function number(value?: string | number | null) {
  return Number(value ?? 0);
}

function commandCenterLoadList(loads: Load[]) {
  return loads
    .map((load, index) => ({ load, index }))
    .sort((left, right) => {
      const leftDemoIndex = demoShowcaseLoadOrder.indexOf(left.load.load_id);
      const rightDemoIndex = demoShowcaseLoadOrder.indexOf(right.load.load_id);
      const leftIsDemo = leftDemoIndex !== -1;
      const rightIsDemo = rightDemoIndex !== -1;

      if (leftIsDemo && rightIsDemo) {
        return leftDemoIndex - rightDemoIndex;
      }
      if (leftIsDemo) {
        return -1;
      }
      if (rightIsDemo) {
        return 1;
      }

      return left.index - right.index;
    })
    .map(({ load }) => load);
}

function readableApiError(error: unknown, fallback: string) {
  if (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    "message" in error
  ) {
    const status = Number((error as { status: unknown }).status);
    const message = (error as { message: unknown }).message;

    if (
      (status === 404 || status === 409 || status === 422) &&
      typeof message === "string"
    ) {
      return message;
    }
  }

  return fallback;
}
