"use client";

import { useEffect, useState } from "react";

type EquipmentType = "Dry Van" | "Reefer" | "Flatbed" | "Power Only";

type LoadEvaluationResult = {
  recommendation: "TAKE" | "REVIEW" | "AVOID";
  metrics: {
    gross_rpm: number;
    deadhead_adjusted_rpm: number;
    estimated_fuel_cost: number;
    estimated_revenue_per_hour: number;
    deadhead_penalty: number;
    operational_score: number;
  };
  reasons: string[];
};

type MockLoad = {
  name: string;
  description: string;
  payout: number;
  loaded_miles: number;
  deadhead_miles: number;
  equipment_type: EquipmentType;
  expected_recommendation: "TAKE" | "REVIEW" | "AVOID";
};

export default function LoadEvaluationPage() {
  const [payout, setPayout] = useState("");
  const [loadedMiles, setLoadedMiles] = useState("");
  const [deadheadMiles, setDeadheadMiles] = useState("");
  const [equipmentType, setEquipmentType] = useState<EquipmentType>("Dry Van");

  const [mockLoads, setMockLoads] = useState<MockLoad[]>([]);
  const [result, setResult] = useState<LoadEvaluationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMockLoads();
  }, []);

  const fetchMockLoads = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/load-evaluation/mock-loads"
      );

      if (!response.ok) {
        throw new Error("Failed to load demo scenarios");
      }

      const data = (await response.json()) as MockLoad[];
      setMockLoads(data);
    } catch (err) {
      console.error(err);
    }
  };

  const evaluateLoad = async () => {
    await evaluateLoadRequest({
      payout: Number(payout),
      loaded_miles: Number(loadedMiles),
      deadhead_miles: Number(deadheadMiles),
      equipment_type: equipmentType,
    });
  };

  const evaluateLoadRequest = async ({
    payout,
    loaded_miles,
    deadhead_miles,
    equipment_type,
  }: {
    payout: number;
    loaded_miles: number;
    deadhead_miles: number;
    equipment_type: EquipmentType;
  }) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await fetch(
        "http://localhost:8000/api/load-evaluation/evaluate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            payout,
            loaded_miles,
            deadhead_miles,
            equipment_type,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to evaluate load");
      }

      const data = (await response.json()) as LoadEvaluationResult;
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected evaluation error"
      );
    } finally {
      setLoading(false);
    }
  };

  const applyScenario = async (load: MockLoad) => {
    setPayout(String(load.payout));
    setLoadedMiles(String(load.loaded_miles));
    setDeadheadMiles(String(load.deadhead_miles));
    setEquipmentType(load.equipment_type);

    await evaluateLoadRequest({
      payout: load.payout,
      loaded_miles: load.loaded_miles,
      deadhead_miles: load.deadhead_miles,
      equipment_type: load.equipment_type,
    });
  };

  const isFormValid =
    Number(payout) > 0 && Number(loadedMiles) > 0 && Number(deadheadMiles) >= 0;

  return (
    <main className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Should We Take This Load?
          </h1>
          <p className="mt-2 text-slate-600">
            Evaluate payout, deadhead, mileage, and equipment fit before
            accepting a load.
          </p>
        </div>

        {mockLoads.length > 0 && (
          <section className="space-y-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Demo Scenarios
              </h2>
              <p className="text-sm text-slate-600">
                Click a scenario to auto-fill and evaluate the load.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              {mockLoads.map((load) => (
                <button
                  key={load.name}
                  type="button"
                  onClick={() => applyScenario(load)}
                  className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-slate-400 hover:shadow-md"
                >
                  <div className="text-sm font-semibold text-slate-900">
                    {load.name}
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    {load.description}
                  </div>
                  <div className="mt-3 text-xs font-medium text-slate-700">
                    Expected: {load.expected_recommendation}
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">
              Load Details
            </h2>

            <div className="mt-6 space-y-4">
              <Input label="Load Payout ($)" value={payout} onChange={setPayout} placeholder="2500" />
              <Input label="Loaded Miles" value={loadedMiles} onChange={setLoadedMiles} placeholder="900" />
              <Input label="Deadhead Miles" value={deadheadMiles} onChange={setDeadheadMiles} placeholder="120" />

              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Equipment Type
                </label>
                <select
                  value={equipmentType}
                  onChange={(e) =>
                    setEquipmentType(e.target.value as EquipmentType)
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option>Dry Van</option>
                  <option>Reefer</option>
                  <option>Flatbed</option>
                  <option>Power Only</option>
                </select>
              </div>

              <button
                type="button"
                onClick={evaluateLoad}
                disabled={!isFormValid || loading}
                className="w-full rounded-xl bg-slate-900 px-4 py-3 font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Evaluating..." : "Evaluate Load"}
              </button>

              {error && (
                <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">
              Recommendation Summary
            </h2>

            {!result ? (
              <div className="mt-6 rounded-xl bg-slate-100 p-6 text-slate-600">
                Enter load details or click a demo scenario to generate a recommendation.
              </div>
            ) : (
              <div className="mt-6 space-y-5">
                <div
                  className={`rounded-2xl p-6 ${
                    result.recommendation === "TAKE"
                      ? "bg-green-50"
                      : result.recommendation === "AVOID"
                        ? "bg-red-50"
                        : "bg-yellow-50"
                  }`}
                >
                  <div className="text-sm font-medium text-slate-600">
                    FleetOS Recommendation
                  </div>
                  <div className="mt-2 text-4xl font-bold text-slate-900">
                    {result.recommendation}
                  </div>
                  <p className="mt-2 text-slate-700">
                    Operational Score: {result.metrics.operational_score}/100
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Metric label="Gross RPM" value={`$${result.metrics.gross_rpm.toFixed(2)}`} />
                  <Metric label="Deadhead Adjusted RPM" value={`$${result.metrics.deadhead_adjusted_rpm.toFixed(2)}`} />
                  <Metric label="Estimated Fuel Cost" value={`$${result.metrics.estimated_fuel_cost.toFixed(2)}`} />
                  <Metric label="Estimated Revenue / Hour" value={`$${result.metrics.estimated_revenue_per_hour.toFixed(2)}`} />
                  <Metric label="Deadhead Penalty" value={`${result.metrics.deadhead_penalty.toFixed(1)}%`} />
                  <Metric label="Operational Score" value={`${result.metrics.operational_score}/100`} />
                </div>

                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="text-sm font-medium text-slate-600">
                    Recommendation Reasons
                  </div>
                  <ul className="mt-3 space-y-2">
                    {result.reasons.map((reason) => (
                      <li key={reason} className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
      />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-bold text-slate-900">{value}</div>
    </div>
  );
}