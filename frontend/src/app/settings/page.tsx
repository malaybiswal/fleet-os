"use client";

import { CheckCircle2, Plug, RefreshCw, TestTube2, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import {
  connectDatCredentials,
  disconnectDat,
  getDatIntegration,
  testDatConnection,
  triggerDatSync,
} from "@/lib/api";
import type { DatIntegrationStatus } from "@/types";

const SYNC_POLL_INTERVAL_MS = 1500;
const SYNC_POLL_ATTEMPTS = 8;

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


export default function SettingsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [status, setStatus] = useState<DatIntegrationStatus | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [originState, setOriginState] = useState("");
  const [destinationState, setDestinationState] = useState("");
  const [equipmentType, setEquipmentType] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);

  async function refreshStatus() {
    const nextStatus = await getDatIntegration();
    setStatus(nextStatus);
  }

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    refreshStatus().catch((err) => {
      console.error(err);
      setError("Failed to load DAT integration status");
    });
  }, [isAuthenticated, isLoading]);

  async function runAction(action: string, callback: () => Promise<void>) {
    setBusyAction(action);
    setMessage("");
    setError("");
    try {
      await callback();
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "DAT request failed");
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
      const nextStatus = await connectDatCredentials({
        username,
        password,
        base_url: baseUrl.trim() || undefined,
        filters,
      });
      setStatus(nextStatus);
      setPassword("");
      setEditing(false);
      setMessage("DAT credentials connected");
    });
  }

  function startEditing() {
    setUsername(status?.username ?? "");
    setBaseUrl(status?.base_url ?? "");
    const filters = status?.filters ?? {};
    setOriginState(filters.origin_state ? String(filters.origin_state) : "");
    setDestinationState(
      filters.destination_state ? String(filters.destination_state) : "",
    );
    setEquipmentType(
      filters.equipment_type ? String(filters.equipment_type) : "",
    );
    setPassword("");
    setMessage("");
    setError("");
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setPassword("");
    setMessage("");
    setError("");
  }

  async function handleTest() {
    await runAction("test", async () => {
      const result = await testDatConnection();
      setMessage(result.message);
      await refreshStatus();
    });
  }

  async function handleSync() {
    await runAction("sync", async () => {
      const prevSyncAt = status?.last_sync_at ?? null;
      const prevError = status?.last_error ?? null;

      // The backend accepts the sync (202) and runs it off the request path, so
      // this call returns immediately even if live DAT is slow or failing.
      await triggerDatSync();
      setMessage("DAT sync started…");

      for (let attempt = 0; attempt < SYNC_POLL_ATTEMPTS; attempt += 1) {
        await delay(SYNC_POLL_INTERVAL_MS);
        const next = await getDatIntegration();
        setStatus(next);

        const settled =
          (next.last_sync_at ?? null) !== prevSyncAt ||
          (next.last_error ?? null) !== prevError;
        if (settled) {
          if (next.last_error) {
            setError(`DAT sync failed: ${next.last_error}`);
            setMessage("");
          } else {
            setMessage("DAT sync complete");
          }
          return;
        }
      }

      setMessage("DAT sync is still running — check back shortly");
    });
  }

  async function handleDisconnect() {
    await runAction("disconnect", async () => {
      const nextStatus = await disconnectDat();
      setStatus(nextStatus);
      setEditing(false);
      setMessage("DAT integration disconnected");
    });
  }

  if (isLoading) {
    return <div className="p-6 text-slate-700">Loading settings...</div>;
  }

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500">Fleet integrations and operational controls</p>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">DAT Integration</h2>
            <p className="text-sm text-slate-500">
              Fleet-scoped load ingestion for dispatcher recommendations
            </p>
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
                <dt className="font-medium text-slate-900">Connected as</dt>
                <dd className="text-slate-600">{status.username || "—"}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-900">Base URL</dt>
                <dd className="text-slate-600">
                  {status.base_url || "Default environment DAT URL"}
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
                Update credentials
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
            Username
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Password
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700 md:col-span-2">
            Base URL
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="Default environment DAT URL"
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
    </main>
  );
}
