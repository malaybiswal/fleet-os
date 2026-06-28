"use client";

import { CheckCircle2, Plug, RefreshCw, TestTube2, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import {
  connectDatCredentials,
  connectTruckstopCredentials,
  disconnectDat,
  disconnectTruckstop,
  getDatIntegration,
  getTruckstopIntegration,
  testDatConnection,
  testTruckstopConnection,
  triggerDatSync,
  triggerTruckstopSync,
} from "@/lib/api";
import type {
  DatIntegrationStatus,
  TruckstopIntegrationStatus,
} from "@/types";

const SYNC_POLL_INTERVAL_MS = 1500;
const SYNC_POLL_ATTEMPTS = 8;

type IntegrationStatus = DatIntegrationStatus | TruckstopIntegrationStatus;

type IntegrationCardConfig = {
  name: "DAT" | "Truckstop";
  title: string;
  description: string;
  accountLabel: string;
  accountAutocomplete: string;
  secretLabel: string;
  userLabel: string;
  userAutocomplete: string;
  urlLabel: string;
  urlPlaceholder: string;
  getStatus: () => Promise<IntegrationStatus>;
  connect: (fields: CredentialFields) => Promise<IntegrationStatus>;
  test: () => Promise<{ success: boolean; message: string }>;
  sync: () => Promise<{ status: string; detail: string }>;
  disconnect: () => Promise<IntegrationStatus>;
  getAccountValue: (status: IntegrationStatus | null) => string;
  getUserValue: (status: IntegrationStatus | null) => string;
};

type CredentialFields = {
  account: string;
  secret: string;
  user: string;
  baseUrl?: string;
  filters: Record<string, unknown>;
};

function isDatStatus(status: IntegrationStatus | null): status is DatIntegrationStatus {
  return Boolean(status && "service_account_email" in status);
}

function isTruckstopStatus(
  status: IntegrationStatus | null,
): status is TruckstopIntegrationStatus {
  return Boolean(status && "integration_id" in status);
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatDate(value?: string | null) {
  if (!value) return "Never";
  return new Date(value).toLocaleString();
}

function formatFilters(filters?: Record<string, unknown>): string {
  if (!filters) return "None";
  const origin = filters.origin_state ? String(filters.origin_state) : "";
  const destination = filters.destination_state
    ? String(filters.destination_state)
    : "";
  const equipment = filters.equipment_type ? String(filters.equipment_type) : "";

  const lane = [origin, destination].filter(Boolean).join(" → ");
  const parts = [lane, equipment].filter(Boolean);
  return parts.length ? parts.join(" · ") : "None";
}

const integrationConfigs: IntegrationCardConfig[] = [
  {
    name: "DAT",
    title: "DAT Integration",
    description: "Fleet-scoped load ingestion for dispatcher recommendations",
    accountLabel: "Service Account Email",
    accountAutocomplete: "username",
    secretLabel: "Service Account Password",
    userLabel: "User Email",
    userAutocomplete: "email",
    urlLabel: "Freight API URL",
    urlPlaceholder: "Default environment DAT URL",
    getStatus: getDatIntegration,
    connect: (fields) =>
      connectDatCredentials({
        service_account_email: fields.account,
        service_account_password: fields.secret,
        user_email: fields.user,
        base_url: fields.baseUrl,
        filters: fields.filters,
      }),
    test: testDatConnection,
    sync: triggerDatSync,
    disconnect: disconnectDat,
    getAccountValue: (status) =>
      isDatStatus(status) ? status.service_account_email ?? "" : "",
    getUserValue: (status) =>
      isDatStatus(status) ? status.user_email ?? "" : "",
  },
  {
    name: "Truckstop",
    title: "Truckstop Integration",
    description: "Carrier load-search ingestion through the provider-neutral layer",
    accountLabel: "Integration ID",
    accountAutocomplete: "off",
    secretLabel: "Password",
    userLabel: "Username",
    userAutocomplete: "username",
    urlLabel: "Truckstop SOAP URL",
    urlPlaceholder: "Default Truckstop staging or production URL",
    getStatus: getTruckstopIntegration,
    connect: (fields) =>
      connectTruckstopCredentials({
        integration_id: fields.account,
        username: fields.user,
        password: fields.secret,
        base_url: fields.baseUrl,
        filters: fields.filters,
      }),
    test: testTruckstopConnection,
    sync: triggerTruckstopSync,
    disconnect: disconnectTruckstop,
    getAccountValue: (status) =>
      isTruckstopStatus(status) ? status.integration_id ?? "" : "",
    getUserValue: (status) =>
      isTruckstopStatus(status) ? status.username ?? "" : "",
  },
];

export default function SettingsPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="p-6 text-slate-700">Loading settings...</div>;
  }

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500">Fleet integrations and operational controls</p>
      </div>

      {integrationConfigs.map((config) => (
        <IntegrationCard
          key={config.name}
          config={config}
          isAuthenticated={isAuthenticated}
        />
      ))}
    </main>
  );
}

function IntegrationCard({
  config,
  isAuthenticated,
}: {
  config: IntegrationCardConfig;
  isAuthenticated: boolean;
}) {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [account, setAccount] = useState("");
  const [secret, setSecret] = useState("");
  const [user, setUser] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [originState, setOriginState] = useState("");
  const [destinationState, setDestinationState] = useState("");
  const [equipmentType, setEquipmentType] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);

  async function refreshStatus() {
    const nextStatus = await config.getStatus();
    setStatus(nextStatus);
  }

  useEffect(() => {
    if (!isAuthenticated) return;
    refreshStatus().catch((err) => {
      console.error(err);
      setError(`Failed to load ${config.name} integration status`);
    });
  }, [config, isAuthenticated]);

  async function runAction(action: string, callback: () => Promise<void>) {
    setBusyAction(action);
    setMessage("");
    setError("");
    try {
      await callback();
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : `${config.name} request failed`);
    } finally {
      setBusyAction(null);
    }
  }

  async function handleConnect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("connect", async () => {
      const filters = Object.fromEntries(
        Object.entries({
          origin_state: originState.trim() || undefined,
          destination_state: destinationState.trim() || undefined,
          equipment_type: equipmentType.trim() || undefined,
        }).filter(([, value]) => value !== undefined),
      );
      const nextStatus = await config.connect({
        account,
        secret,
        user,
        baseUrl: baseUrl.trim() || undefined,
        filters,
      });
      setStatus(nextStatus);
      setSecret("");
      setEditing(false);
      setMessage(`${config.name} credentials connected`);
    });
  }

  function startEditing() {
    setAccount(config.getAccountValue(status));
    setUser(config.getUserValue(status));
    setBaseUrl(status?.base_url ?? "");
    const filters = status?.filters ?? {};
    setOriginState(filters.origin_state ? String(filters.origin_state) : "");
    setDestinationState(
      filters.destination_state ? String(filters.destination_state) : "",
    );
    setEquipmentType(
      filters.equipment_type ? String(filters.equipment_type) : "",
    );
    setSecret("");
    setMessage("");
    setError("");
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setSecret("");
    setMessage("");
    setError("");
  }

  async function handleTest() {
    await runAction("test", async () => {
      const result = await config.test();
      setMessage(result.message);
      await refreshStatus();
    });
  }

  async function handleSync() {
    await runAction("sync", async () => {
      const prevSyncAt = status?.last_sync_at ?? null;
      const prevError = status?.last_error ?? null;

      await config.sync();
      setMessage(`${config.name} sync started...`);

      for (let attempt = 0; attempt < SYNC_POLL_ATTEMPTS; attempt += 1) {
        await delay(SYNC_POLL_INTERVAL_MS);
        const next = await config.getStatus();
        setStatus(next);

        const settled =
          (next.last_sync_at ?? null) !== prevSyncAt ||
          (next.last_error ?? null) !== prevError;
        if (settled) {
          if (next.last_error) {
            setError(`${config.name} sync failed: ${next.last_error}`);
            setMessage("");
          } else {
            setMessage(`${config.name} sync complete`);
          }
          return;
        }
      }

      setMessage(`${config.name} sync is still running - check back shortly`);
    });
  }

  async function handleDisconnect() {
    await runAction("disconnect", async () => {
      const nextStatus = await config.disconnect();
      setStatus(nextStatus);
      setEditing(false);
      setMessage(`${config.name} integration disconnected`);
    });
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{config.title}</h2>
          <p className="text-sm text-slate-500">{config.description}</p>
        </div>
        <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
          <CheckCircle2 className="h-4 w-4" />
          {status?.connected ? status.status : "not_connected"}
        </div>
      </div>

      {status?.connected && !editing ? (
        <div className="space-y-5">
          <dl className="grid gap-4 text-sm md:grid-cols-2">
            <div>
              <dt className="font-medium text-slate-900">{config.accountLabel}</dt>
              <dd className="text-slate-600">
                {config.getAccountValue(status) || "—"}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-900">{config.userLabel}</dt>
              <dd className="text-slate-600">
                {config.getUserValue(status) || "—"}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-900">{config.urlLabel}</dt>
              <dd className="text-slate-600">
                {status.base_url || config.urlPlaceholder}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-900">Filters</dt>
              <dd className="text-slate-600">{formatFilters(status.filters)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-900">Last sync</dt>
              <dd className="text-slate-600">{formatDate(status.last_sync_at)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-900">Last error</dt>
              <dd className="text-slate-600">{status.last_error || "None"}</dd>
            </div>
          </dl>

          <div className="flex flex-wrap gap-3">
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
              disabled={busyAction !== null}
              type="button"
              onClick={handleTest}
            >
              <TestTube2 className="h-4 w-4" />
              {busyAction === "test" ? "Testing..." : "Test"}
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
              disabled={busyAction !== null}
              type="button"
              onClick={handleSync}
            >
              <RefreshCw className="h-4 w-4" />
              {busyAction === "sync" ? "Syncing..." : "Sync now"}
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
              disabled={busyAction !== null}
              type="button"
              onClick={startEditing}
            >
              <Plug className="h-4 w-4" />
              Update {config.name} credentials
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-60"
              disabled={busyAction !== null}
              type="button"
              onClick={handleDisconnect}
            >
              <Trash2 className="h-4 w-4" />
              Disconnect
            </button>
          </div>
        </div>
      ) : (
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleConnect}>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            {config.accountLabel}
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={account}
              onChange={(event) => setAccount(event.target.value)}
              autoComplete={config.accountAutocomplete}
              required
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            {config.secretLabel}
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={secret}
              onChange={(event) => setSecret(event.target.value)}
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700 md:col-span-2">
            {config.userLabel}
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={user}
              onChange={(event) => setUser(event.target.value)}
              autoComplete={config.userAutocomplete}
              type={config.userAutocomplete === "email" ? "email" : "text"}
              required
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700 md:col-span-2">
            {config.urlLabel}
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder={config.urlPlaceholder}
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Origin State
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={originState}
              onChange={(event) => setOriginState(event.target.value)}
              maxLength={2}
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Destination State
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={destinationState}
              onChange={(event) => setDestinationState(event.target.value)}
              maxLength={2}
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700 md:col-span-2">
            Equipment
            <select
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900"
              value={equipmentType}
              onChange={(event) => setEquipmentType(event.target.value)}
            >
              <option value="">Any</option>
              <option value="Dry Van">Dry Van</option>
              <option value="Reefer">Reefer</option>
              <option value="Flatbed">Flatbed</option>
              <option value="Power Only">Power Only</option>
            </select>
          </label>

          <div className="flex flex-wrap gap-3 md:col-span-2">
            <button
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              disabled={busyAction !== null}
              type="submit"
            >
              <Plug className="h-4 w-4" />
              {busyAction === "connect" ? "Connecting..." : "Connect"}
            </button>
            {editing ? (
              <button
                className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
                disabled={busyAction !== null}
                type="button"
                onClick={cancelEditing}
              >
                Cancel
              </button>
            ) : null}
          </div>
        </form>
      )}

      {message ? <p className="mt-4 text-sm font-medium text-green-700">{message}</p> : null}
      {error ? <p className="mt-4 text-sm font-medium text-red-700">{error}</p> : null}
    </section>
  );
}
