import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DemoStoryCard } from "./DemoStoryCard";
import { DEMO_STORIES } from "./demoStories";
import type { EvaluatedMockLoad } from "@/types";

afterEach(() => {
  cleanup();
});

describe("DemoStoryCard", () => {
  it("renders the story title, talking points, and CTA link", () => {
    const story = DEMO_STORIES.find((s) => s.key === "bad_load")!;
    render(<DemoStoryCard story={story} />);

    expect(screen.getByText(story.title)).toBeTruthy();
    story.talkingPoints.forEach((point) => {
      expect(screen.getByText(point)).toBeTruthy();
    });

    const cta = screen.getByText(`${story.cta.label} →`).closest("a");
    expect(cta?.getAttribute("href")).toBe(story.cta.href);
  });

  it("renders the secondary CTA when present", () => {
    const story = DEMO_STORIES.find((s) => s.key === "alerting")!;
    render(<DemoStoryCard story={story} />);

    const secondary = screen.getByText(story.secondaryCta!.label).closest("a");
    expect(secondary?.getAttribute("href")).toBe(story.secondaryCta!.href);
  });

  it("shows the live recommendation and score when a mock load is provided", () => {
    const story = DEMO_STORIES.find((s) => s.key === "good_load")!;
    const mockLoad: EvaluatedMockLoad = {
      name: "Low Pay / Good Load",
      description: "Lower gross payout, but short miles and low deadhead.",
      payout: 950,
      loaded_miles: 260,
      deadhead_miles: 20,
      equipment_type: "Dry Van",
      expected_recommendation: "TAKE",
      actual_recommendation: "TAKE",
      metrics: {
        gross_rpm: 3.65,
        deadhead_adjusted_rpm: 3.39,
        estimated_fuel_cost: 160,
        estimated_revenue_per_hour: 186.27,
        deadhead_penalty: 7.1,
        operational_score: 88,
      },
      reasons: ["Strong deadhead-adjusted RPM"],
      destination_facility: null,
    };

    render(<DemoStoryCard story={story} mockLoad={mockLoad} />);

    expect(screen.getByText("TAKE")).toBeTruthy();
    expect(screen.getByText(/Score 88\/100/)).toBeTruthy();
    expect(screen.getByText(/\$3\.39\/mi adj\. RPM/)).toBeTruthy();
  });
});
