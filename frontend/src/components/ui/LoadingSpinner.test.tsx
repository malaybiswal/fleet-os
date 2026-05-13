import React from "react";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LoadingSpinner } from "./LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders a spinning element", () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeTruthy();
  });
});
