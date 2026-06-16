import type { DemoStory } from "./demoStories";

/**
 * TASK-037D — 60-Second Micro Demo Script.
 *
 * A single, linear, time-boxed cold-outreach flow (~60s total) for a first call
 * with a prospect who has never seen FleetOS. Each beat is one of the five GTM
 * focus pillars from the spec, lands on a real product surface, and — where it
 * makes sense — reuses the 037C demo story library so copy never diverges.
 */
export type MicroDemoBeat = {
  id: string;
  /** GTM pillar this beat delivers (from the TASK-037D "Focus" list). */
  focus: string;
  /** Roughly how long the presenter spends here; the five sum to ~60s. */
  seconds: number;
  headline: string;
  /** The single line the presenter says out loud. */
  script: string;
  /** Optional supporting scenario from the 037C library (by DemoStory.key). */
  storyKey?: DemoStory["key"];
  /** Deep link into the live product surface for this beat. */
  cta: { href: string; label: string };
};

export const MICRO_DEMO_BEATS: MicroDemoBeat[] = [
  {
    id: "pain",
    focus: "Dispatcher pain",
    seconds: 10,
    headline: "The load that looks great on paper",
    script:
      "Most dispatchers book the load with the biggest payout number — a $4,200 line haul — without ever checking what it really costs to run.",
    storyKey: "bad_load",
    cta: {
      href: "/load-evaluation?scenario=High+Pay+%2F+Bad+Load",
      label: "Show the load",
    },
  },
  {
    id: "visibility",
    focus: "Operational visibility",
    seconds: 12,
    headline: "One live control tower",
    script:
      "First, FleetOS puts your whole fleet on one live map — every truck, its status, and where it's heading, updating in real time.",
    cta: { href: "/live", label: "Open Live Map" },
  },
  {
    id: "decision",
    focus: "Decision intelligence",
    seconds: 14,
    headline: "Should we take this load?",
    script:
      "Drop in any load and FleetOS answers the only question that matters — a clear TAKE or AVOID, with the operational reasons behind it.",
    storyKey: "bad_load",
    cta: { href: "/load-evaluation", label: "Open Load Evaluation" },
  },
  {
    id: "dwell",
    focus: "Dwell prediction",
    seconds: 12,
    headline: "The facility that eats your schedule",
    script:
      "It also flags facilities with chronic detention risk — so you see the dwell problem before you ever commit a truck to it.",
    storyKey: "high_dwell",
    cta: { href: "/dwell", label: "Open Dwell Analytics" },
  },
  {
    id: "profitability",
    focus: "Profitability optimization",
    seconds: 12,
    headline: "Revenue per hour, not per mile",
    script:
      "Underneath it all FleetOS optimizes revenue per hour — so that 'great' $4,200 load gets flagged AVOID once deadhead and time are priced in.",
    storyKey: "bad_load",
    cta: {
      href: "/load-evaluation?scenario=High+Pay+%2F+Bad+Load",
      label: "See the economics",
    },
  },
];

export const MICRO_DEMO_TOTAL_SECONDS = MICRO_DEMO_BEATS.reduce(
  (total, beat) => total + beat.seconds,
  0,
);
