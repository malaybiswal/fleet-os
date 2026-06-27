import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "./page";
import type { DatIntegrationStatus } from "@/types";

const apiMocks = vi.hoisted(() => ({
  getDatIntegration: vi.fn(),
  connectDatCredentials: vi.fn(),
  testDatConnection: vi.fn(),
  triggerDatSync: vi.fn(),
  disconnectDat: vi.fn(),
}));

const authMocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
}));

vi.mock("@/lib/api", () => apiMocks);

vi.mock("@/components/auth/AuthProvider", () => ({
  useAuth: authMocks.useAuth,
}));

afterEach(() => {
  cleanup();
});

const connectedStatus: DatIntegrationStatus = {
  connected: true,
  status: "connected",
  last_sync_at: "2026-06-26T17:42:00Z",
  last_error: null,
  service_account_email: "service@dat.example",
  user_email: "user@dat.example",
  base_url: "https://api.dat.com",
  filters: { origin_state: "TX", destination_state: "AZ", equipment_type: "Reefer" },
};

const notConnectedStatus: DatIntegrationStatus = {
  connected: false,
  status: "not_connected",
};

beforeEach(() => {
  vi.clearAllMocks();
  authMocks.useAuth.mockReturnValue({ isAuthenticated: true, isLoading: false });
});

describe("SettingsPage DAT integration", () => {
  it("shows a connected summary and hides the credential form", async () => {
    apiMocks.getDatIntegration.mockResolvedValue(connectedStatus);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("service@dat.example")).toBeTruthy();
    });
    expect(screen.getByText("Service account")).toBeTruthy();
    expect(screen.getByText("user@dat.example")).toBeTruthy();
    expect(screen.getByText("https://api.dat.com")).toBeTruthy();
    expect(screen.getByText("TX → AZ · Reefer")).toBeTruthy();
    // Credential inputs are not rendered while connected.
    expect(screen.queryByLabelText(/Service Account Email/i)).toBeNull();
  });

  it("reveals a pre-filled form when updating credentials, without the password", async () => {
    apiMocks.getDatIntegration.mockResolvedValue(connectedStatus);

    render(<SettingsPage />);

    await waitFor(() => expect(screen.getByText("service@dat.example")).toBeTruthy());
    fireEvent.click(screen.getByText("Update credentials"));

    const serviceAccountEmail = screen.getByLabelText(
      /Service Account Email/i,
    ) as HTMLInputElement;
    const userEmail = screen.getByLabelText(/User Email/i) as HTMLInputElement;
    const password = screen.getByLabelText(/Service Account Password/i) as HTMLInputElement;
    expect(serviceAccountEmail.value).toBe("service@dat.example");
    expect(userEmail.value).toBe("user@dat.example");
    expect(password.value).toBe("");
  });

  it("shows the credential form when not connected", async () => {
    apiMocks.getDatIntegration.mockResolvedValue(notConnectedStatus);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Service Account Email/i)).toBeTruthy();
    });
    expect(screen.queryByText("Service account")).toBeNull();
  });
});
