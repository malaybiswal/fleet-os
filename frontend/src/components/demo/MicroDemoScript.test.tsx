import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { MicroDemoScript } from "./MicroDemoScript";
import { MICRO_DEMO_BEATS, MICRO_DEMO_TOTAL_SECONDS } from "./microDemoBeats";

afterEach(() => {
  cleanup();
});

describe("microDemoScript data", () => {
  it("is a five-beat, ~60-second flow", () => {
    expect(MICRO_DEMO_BEATS).toHaveLength(5);
    expect(MICRO_DEMO_TOTAL_SECONDS).toBe(60);
  });
});

describe("MicroDemoScript", () => {
  it("opens on the first beat with its script and deep-link CTA", () => {
    render(<MicroDemoScript />);

    const first = MICRO_DEMO_BEATS[0];
    expect(screen.getByText(first.headline)).toBeTruthy();
    expect(screen.getByText(first.script)).toBeTruthy();
    expect(screen.getByText("Beat 1 of 5")).toBeTruthy();

    const cta = screen.getByText(`${first.cta.label} →`).closest("a");
    expect(cta?.getAttribute("href")).toBe(first.cta.href);
  });

  it("advances to the next beat when Next is clicked", () => {
    render(<MicroDemoScript />);

    fireEvent.click(screen.getByText("Next →"));

    const second = MICRO_DEMO_BEATS[1];
    expect(screen.getByText(second.headline)).toBeTruthy();
    expect(screen.getByText("Beat 2 of 5")).toBeTruthy();
  });

  it("jumps directly to a beat from its progress marker", () => {
    render(<MicroDemoScript />);

    const last = MICRO_DEMO_BEATS[MICRO_DEMO_BEATS.length - 1];
    fireEvent.click(
      screen.getByLabelText(`Go to beat 5: ${last.focus}`),
    );

    expect(screen.getByText(last.headline)).toBeTruthy();
    expect(screen.getByText("Beat 5 of 5")).toBeTruthy();
  });
});
