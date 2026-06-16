export type DemoStoryAccent = "red" | "green" | "amber" | "blue";

export type DemoStory = {
  key: string;
  title: string;
  tagline: string;
  pain: string;
  insight: string;
  outcome: string;
  talkingPoints: string[];
  /** Matches an EvaluatedMockLoad.name from /api/load-evaluation/mock-loads */
  scenarioName?: string;
  accent: DemoStoryAccent;
  cta: { href: string; label: string };
  secondaryCta?: { href: string; label: string };
};

export const DEMO_STORIES: DemoStory[] = [
  {
    key: "bad_load",
    title: "The Load That Looks Great on Paper",
    tagline: "A high-payout load that quietly destroys your margins.",
    pain: "Dispatchers see a big payout number and book the load without checking deadhead or time cost.",
    insight: "FleetOS recalculates the deadhead-adjusted RPM and revenue/hour, exposing the real economics behind the headline payout.",
    outcome: "FleetOS recommends AVOID before the truck ever rolls.",
    talkingPoints: [
      "$4,200 payout looks attractive at first glance",
      "550 miles of deadhead drags the adjusted RPM down to $2.05/mi",
      "Revenue/hour drops to ~$113 once total drive time is factored in",
      "Operational score lands in AVOID territory — dispatcher is warned before accepting",
    ],
    scenarioName: "High Pay / Bad Load",
    accent: "red",
    cta: { href: "/load-evaluation?scenario=High+Pay+%2F+Bad+Load", label: "Open Load Evaluation" },
  },
  {
    key: "good_load",
    title: "The Short-Haul Everyone Overlooks",
    tagline: "A modest payout that's operationally one of the best loads available.",
    pain: "Lower gross revenue loads get passed over even when they're the most profitable option per hour.",
    insight: "FleetOS surfaces deadhead-adjusted RPM and revenue/hour so short, efficient loads get the credit they deserve.",
    outcome: "FleetOS recommends TAKE with a strong operational score.",
    talkingPoints: [
      "$950 payout, but only 20 miles of deadhead",
      "Deadhead-adjusted RPM of $3.39/mi — among the best available",
      "Revenue/hour of ~$186 thanks to the short total distance",
      "Operational score lands comfortably in TAKE territory",
    ],
    scenarioName: "Low Pay / Good Load",
    accent: "green",
    cta: { href: "/load-evaluation?scenario=Low+Pay+%2F+Good+Load", label: "Open Load Evaluation" },
  },
  {
    key: "high_dwell",
    title: "The Facility That Eats Your Schedule",
    tagline: "Solid lane economics undone by a facility with chronic dwell problems.",
    pain: "Dispatchers evaluate a load on miles and rate alone, with no visibility into how long trucks actually sit at the destination.",
    insight: "FleetOS's Facility Intelligence Engine tracks dwell history and detention risk per facility, independent of any single load.",
    outcome: "Dallas Mega Cold Storage shows a high detention-risk badge wherever it appears — on the load card and the facility scorecard.",
    talkingPoints: [
      "Load economics alone look acceptable: $2,400 payout, only 90 miles of deadhead",
      "Destination is Dallas Mega Cold Storage — recent visits average 7+ hours of dwell",
      "Detention risk score lands in the HIGH band based on real visit history",
      "Dispatcher sees the risk badge before committing the truck",
    ],
    scenarioName: "High Dwell Risk",
    accent: "amber",
    cta: { href: "/dwell", label: "Open Dwell Analytics" },
    secondaryCta: { href: "/load-evaluation?scenario=High+Dwell+Risk", label: "View load evaluation" },
  },
  {
    key: "alerting",
    title: "The Fleet That Tells You What's Wrong",
    tagline: "Live telemetry turns into operational alerts the moment something needs attention.",
    pain: "Without live monitoring, a speeding truck, an overdue maintenance stop, or a truck stuck idle goes unnoticed until it's a bigger problem.",
    insight: "FleetOS evaluates every telemetry event against operational rules — speeding, maintenance status, idle and stopped duration — and raises alerts automatically.",
    outcome: "Active alerts appear on the Alerts page and as live badges on the fleet map.",
    talkingPoints: [
      "A truck running 67 mph triggers a SPEEDING alert automatically",
      "A truck flagged for maintenance is surfaced immediately, regardless of speed",
      "Trucks idle or stopped past threshold raise IDLE_TOO_LONG / STOPPED_TOO_LONG alerts",
      "Every alert is fleet-scoped, severity-ranked, and resolvable from one screen",
    ],
    accent: "blue",
    cta: { href: "/alerts", label: "Open Alerts" },
    secondaryCta: { href: "/live", label: "View Live Map" },
  },
];
