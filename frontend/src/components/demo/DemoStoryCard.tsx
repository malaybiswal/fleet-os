import Link from "next/link";

import FacilityRiskBadge from "@/components/ui/FacilityRiskBadge";
import type { EvaluatedMockLoad } from "@/types";
import type { DemoStory, DemoStoryAccent } from "./demoStories";

const ACCENT_STYLES: Record<DemoStoryAccent, string> = {
  red: "border-l-red-400",
  green: "border-l-green-400",
  amber: "border-l-amber-400",
  blue: "border-l-blue-400",
};

const RECOMMENDATION_STYLES: Record<string, string> = {
  RECOMMENDED: "bg-green-100 text-green-700",
  AVOID: "bg-red-100 text-red-700",
  REVIEW: "bg-amber-100 text-amber-700",
};

export function DemoStoryCard({
  story,
  mockLoad,
}: {
  story: DemoStory;
  mockLoad?: EvaluatedMockLoad | null;
}) {
  return (
    <div
      className={`flex flex-col rounded-xl border border-slate-200 border-l-4 bg-white p-5 shadow-sm ${ACCENT_STYLES[story.accent]}`}
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{story.title}</h3>
        <p className="mt-1 text-sm text-slate-500">{story.tagline}</p>
      </div>

      <div className="mt-4 space-y-3 text-sm">
        <Section label="Pain" text={story.pain} />
        <Section label="FleetOS Insight" text={story.insight} />
        <Section label="Outcome" text={story.outcome} />
      </div>

      <ul className="mt-4 space-y-1.5">
        {story.talkingPoints.map((point) => (
          <li key={point} className="flex gap-2 text-xs text-slate-600">
            <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-slate-300" />
            <span>{point}</span>
          </li>
        ))}
      </ul>

      {mockLoad && (
        <div className="mt-4 flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2">
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
              RECOMMENDATION_STYLES[mockLoad.actual_recommendation] ?? "bg-slate-100 text-slate-600"
            }`}
          >
            {mockLoad.actual_recommendation}
          </span>
          <span className="text-xs text-slate-500">
            Profitability {mockLoad.metrics.profitability_score.toFixed(0)}/100 · ${mockLoad.metrics.deadhead_adjusted_rpm.toFixed(2)}/mi adj. RPM
          </span>
          {mockLoad.destination_facility && (
            <FacilityRiskBadge facilityRisk={mockLoad.destination_facility} />
          )}
        </div>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
        <Link
          href={story.cta.href}
          className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          {story.cta.label} →
        </Link>
        {story.secondaryCta && (
          <Link
            href={story.secondaryCta.href}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            {story.secondaryCta.label}
          </Link>
        )}
      </div>
    </div>
  );
}

function Section({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{label}</div>
      <p className="mt-0.5 text-sm text-slate-700">{text}</p>
    </div>
  );
}
