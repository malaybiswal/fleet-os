import React from "react";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CarrierDetailPanel } from "./CarrierDetailPanel";
import type { CarrierDetail, OutreachNote, Tag } from "@/types";

vi.mock("@/lib/api", () => ({
  getCarrier: vi.fn(),
  listNotes: vi.fn(),
  listTags: vi.fn(),
  listCarrierTags: vi.fn(),
  updateOutreachStatus: vi.fn(),
  createNote: vi.fn(),
  deleteNote: vi.fn(),
  updateNote: vi.fn(),
  addTagToCarrier: vi.fn(),
  removeTagFromCarrier: vi.fn(),
  createTag: vi.fn(),
}));

import * as api from "@/lib/api";

const mockCarrier: CarrierDetail = {
  id: 1,
  dot_number: "123456",
  mc_number: "MC-999",
  legal_name: "ACME Freight LLC",
  dba_name: null,
  phone: "555-1234",
  email: "acme@example.com",
  address_line1: "100 Main St",
  city: "Austin",
  state: "TX",
  postal_code: "78701",
  country: "US",
  authority_status: "active",
  authority_date: null,
  power_units: 10,
  driver_count: 8,
  cargo_types: ["General Freight"],
  outreach_status: "not_contacted",
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const mockNote: OutreachNote = {
  id: 10,
  carrier_id: 1,
  content: "Spoke to dispatcher",
  outcome: "interested",
  follow_up_date: null,
  contact_name: null,
  dispatcher_name: "John",
  pain_points: null,
  created_by: null,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const mockTag: Tag = { id: 5, name: "hotshot", display_name: "Hotshot", created_at: "", updated_at: "" };

beforeEach(() => {
  vi.mocked(api.getCarrier).mockResolvedValue(mockCarrier);
  vi.mocked(api.listNotes).mockResolvedValue([]);
  vi.mocked(api.listTags).mockResolvedValue([mockTag]);
  vi.mocked(api.listCarrierTags).mockResolvedValue([]);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CarrierDetailPanel", () => {
  it("renders nothing when carrierId is null", () => {
    const { container } = render(
      <CarrierDetailPanel carrierId={null} onClose={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
    expect(api.getCarrier).not.toHaveBeenCalled();
  });

  it("fetches carrier data and renders carrier name when carrierId is set", async () => {
    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("ACME Freight LLC")).toBeTruthy());
    expect(api.getCarrier).toHaveBeenCalledWith(1);
  });

  it("calls onClose when backdrop is clicked", async () => {
    const onClose = vi.fn();
    render(<CarrierDetailPanel carrierId={1} onClose={onClose} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));
    fireEvent.click(document.querySelector(".fixed.inset-0") as Element);
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when the × button is clicked", async () => {
    const onClose = vi.fn();
    render(<CarrierDetailPanel carrierId={1} onClose={onClose} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalled();
  });

  it("changing outreach status calls updateOutreachStatus and fires onCarrierUpdated", async () => {
    const updated = { ...mockCarrier, outreach_status: "contacted" };
    vi.mocked(api.updateOutreachStatus).mockResolvedValue(updated);
    const onCarrierUpdated = vi.fn();

    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} onCarrierUpdated={onCarrierUpdated} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "contacted" },
    });

    await waitFor(() => expect(api.updateOutreachStatus).toHaveBeenCalledWith(1, "contacted"));
    expect(onCarrierUpdated).toHaveBeenCalledWith(updated);
  });
});

describe("NoteForm", () => {
  beforeEach(() => {
    vi.mocked(api.listNotes).mockResolvedValue([mockNote]);
  });

  it("Add Note button is disabled when content is empty", async () => {
    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));
    const btn = screen.getByRole("button", { name: "Add Note" }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("Add Note button is disabled when content is only whitespace", async () => {
    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));
    fireEvent.change(screen.getByPlaceholderText("Note…"), { target: { value: "   " } });
    const btn = screen.getByRole("button", { name: "Add Note" }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("submitting NoteForm calls createNote and resets the textarea", async () => {
    const newNote: OutreachNote = { ...mockNote, id: 99, content: "New note" };
    vi.mocked(api.createNote).mockResolvedValue(newNote);

    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));

    fireEvent.change(screen.getByPlaceholderText("Note…"), { target: { value: "New note" } });
    fireEvent.submit(screen.getByPlaceholderText("Note…").closest("form")!);

    await waitFor(() => expect(api.createNote).toHaveBeenCalledWith(1, expect.objectContaining({ content: "New note" })));
    await waitFor(() => expect((screen.getByPlaceholderText("Note…") as HTMLTextAreaElement).value).toBe(""));
  });
});

describe("NoteItem", () => {
  beforeEach(() => {
    vi.mocked(api.listNotes).mockResolvedValue([mockNote]);
  });

  it("renders note content", async () => {
    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("Spoke to dispatcher"));
  });

  it("Delete calls deleteNote and removes the note from the list", async () => {
    vi.mocked(api.deleteNote).mockResolvedValue(undefined);
    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("Spoke to dispatcher"));

    fireEvent.click(screen.getByText("Delete"));

    await waitFor(() => expect(api.deleteNote).toHaveBeenCalledWith(1, 10));
    expect(screen.queryByText("Spoke to dispatcher")).toBeNull();
  });

  it("Edit → Save calls updateNote and shows updated content", async () => {
    const updated = { ...mockNote, content: "Updated note" };
    vi.mocked(api.updateNote).mockResolvedValue(updated);

    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("Spoke to dispatcher"));

    fireEvent.click(screen.getByText("Edit"));
    const textarea = screen.getByDisplayValue("Spoke to dispatcher");
    fireEvent.change(textarea, { target: { value: "Updated note" } });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => expect(api.updateNote).toHaveBeenCalledWith(1, 10, { content: "Updated note" }));
    await waitFor(() => expect(screen.getByText("Updated note")).toBeTruthy());
  });
});

describe("TagsSection", () => {
  it("filters out already-applied tags from the suggestions list", async () => {
    const alreadyApplied: Tag = { id: 5, name: "hotshot", display_name: "Hotshot", created_at: "", updated_at: "" };
    const available: Tag = { id: 6, name: "reefer", display_name: "Reefer", created_at: "", updated_at: "" };

    vi.mocked(api.listTags).mockResolvedValue([alreadyApplied, available]);
    vi.mocked(api.listCarrierTags).mockResolvedValue([alreadyApplied]);

    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));

    fireEvent.click(screen.getByText("+ Add tag"));
    fireEvent.change(screen.getByPlaceholderText("Tag name…"), { target: { value: "" } });

    // "Hotshot" chip is visible (applied tag), but must not appear as a suggestion button
    expect(screen.queryByRole("button", { name: "Hotshot" })).toBeNull();
    expect(screen.getByRole("button", { name: "Reefer" })).toBeTruthy();
  });

  it("shows Create button only when typed name does not match an existing tag", async () => {
    vi.mocked(api.listTags).mockResolvedValue([mockTag]);
    vi.mocked(api.listCarrierTags).mockResolvedValue([]);

    render(<CarrierDetailPanel carrierId={1} onClose={vi.fn()} />);
    await waitFor(() => screen.getByText("ACME Freight LLC"));

    fireEvent.click(screen.getByText("+ Add tag"));

    // Typing an existing tag name should NOT show Create button
    fireEvent.change(screen.getByPlaceholderText("Tag name…"), { target: { value: "Hotshot" } });
    expect(screen.queryByText(/Create "Hotshot"/)).toBeNull();

    // Typing a new name should show Create button
    fireEvent.change(screen.getByPlaceholderText("Tag name…"), { target: { value: "flatbed" } });
    expect(screen.getByText(/Create "flatbed"/)).toBeTruthy();
  });
});
