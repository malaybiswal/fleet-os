import React from "react";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CarrierSearchBox } from "./CarrierSearchBox";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("CarrierSearchBox", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("renders the input with the provided value", () => {
    render(<CarrierSearchBox value="ACME" onChange={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Search by company/i) as HTMLInputElement;
    expect(input.value).toBe("ACME");
  });

  it("debounces onChange — fires once after 300ms, not on every keystroke", () => {
    const onChange = vi.fn();
    render(<CarrierSearchBox value="" onChange={onChange} />);
    const input = screen.getByPlaceholderText(/Search by company/i);

    fireEvent.change(input, { target: { value: "A" } });
    fireEvent.change(input, { target: { value: "AC" } });
    fireEvent.change(input, { target: { value: "ACM" } });

    expect(onChange).not.toHaveBeenCalled();

    vi.advanceTimersByTime(300);

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith("ACM");
  });

  it("updates draft immediately on type without waiting for debounce", () => {
    render(<CarrierSearchBox value="" onChange={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Search by company/i) as HTMLInputElement;

    fireEvent.change(input, { target: { value: "TX" } });

    expect(input.value).toBe("TX");
  });

  it("syncs draft when value prop changes externally", () => {
    const { rerender } = render(<CarrierSearchBox value="old" onChange={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Search by company/i) as HTMLInputElement;

    expect(input.value).toBe("old");

    rerender(<CarrierSearchBox value="" onChange={vi.fn()} />);

    expect(input.value).toBe("");
  });

  it("clear button calls onChange('') immediately without waiting for debounce", () => {
    const onChange = vi.fn();
    render(<CarrierSearchBox value="ACM" onChange={onChange} />);

    fireEvent.click(screen.getByLabelText("Clear search"));

    expect(onChange).toHaveBeenCalledWith("");
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("clear button is not shown when input is empty", () => {
    render(<CarrierSearchBox value="" onChange={vi.fn()} />);
    expect(screen.queryByLabelText("Clear search")).toBeNull();
  });
});
