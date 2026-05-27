"use client";

import { useMemo, useState } from "react";

type EquipmentType = "Dry Van" | "Reefer" | "Flatbed" | "Power Only";

export default function LoadEvaluationPage() {
  const [payout, setPayout] = useState("");
  const [loadedMiles, setLoadedMiles] = useState("");
  const [deadheadMiles, setDeadheadMiles] = useState("");
  const [equipmentType, setEquipmentType] = useState<EquipmentType>("Dry Van");

  const result = useMemo(() => {
    const pay = Number(payout);
    const loaded = Number(loadedMiles);
    const deadhead = Number(deadheadMiles);
    const totalMiles = loaded + deadhead;

    if (!pay || !loaded || totalMiles <= 0) {
      return null;
    }

    const rpm = pay / loaded;
    const adjustedRpm = pay / totalMiles;
    const deadheadPercent = (deadhead / totalMiles) * 100;

    let recommendation: "TAKE" | "REVIEW" | "AVOID" = "REVIEW";
    let reason = "This load needs dispatcher review.";

    if (adjustedRpm >= 2.2 && deadheadPercent <= 20) {
      recommendation = "TAKE";
      reason = "Strong deadhead-adjusted revenue per mile.";
    } else if (adjustedRpm < 1.6 || deadheadPercent > 35) {
      recommendation = "AVOID";
      reason = "Weak operational economics after deadhead.";
    }

    return {
      totalMiles,
      rpm,
      adjustedRpm,
      deadheadPercent,
      recommendation,
      reason,
    };
  }, [payout, loadedMiles, deadheadMiles]);

  return (
    <main className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Should We Take This Load?
          </h1>
          <p className="mt-2 text-slate-600">
            Evaluate payout, deadhead, mileage, and equipment fit before accepting a load.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold text-slate-900">
              Load Details
            </h2>

            <div className="mt-6 space-y-4">
              <Input
                label="Load Payout ($)"
                value={payout}
                onChange={setPayout}
                placeholder="2500"
              />

              <Input
                label="Loaded Miles"
                value={loadedMiles}
                onChange={setLoadedMiles}
                placeholder="900"
              />

              <Input
                label="Deadhead Miles"
                value={deadheadMiles}
                onChange={setDeadheadMiles}
                placeholder="120"
              />

              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Equipment Type
                </label>
                <select
                  value={equipmentType}
                  onChange={(e) => setEquipmentType(e.target.value as EquipmentType)}
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option>Dry Van</option>
                  <option>Reefer</option>
                  <option>Flatbed</option>
                  <option>Power Only</option>
                </select>
              </div>
            </div>
          </section>

          <section className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold text-slate-900">
              Recommendation Summary
            </h2>

            {!result ? (
              <div className="mt-6 rounded-xl bg-slate-100 p-6 text-slate-600">
                Enter load details to generate a recommendation.
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
                  <p className="mt-2 text-slate-700">{result.reason}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Metric label="Revenue / Loaded Mile" value={`$${result.rpm.toFixed(2)}`} />
                  <Metric label="Deadhead Adjusted RPM" value={`$${result.adjustedRpm.toFixed(2)}`} />
                  <Metric label="Total Miles" value={result.totalMiles.toFixed(0)} />
                  <Metric label="Deadhead %" value={`${result.deadheadPercent.toFixed(1)}%`} />
                </div>

                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="text-sm text-slate-500">Equipment</div>
                  <div className="mt-1 font-semibold text-slate-900">
                    {equipmentType}
                  </div>
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
