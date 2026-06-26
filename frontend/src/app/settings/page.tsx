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
import type { DatIntegrationStatus, DatSyncResponse } from "@/types";


function formatDate(value?: string | null) {
  if (!value) return "Never";
  return new Date(value).toLocaleString();
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
  const [lastSync, setLastSync] = useState<DatSyncResponse | null>(null);

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
      setMessage("DAT credentials connected");
    });
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
      const result = await triggerDatSync();
      setLastSync(result);
      setMessage(`DAT sync ingested ${result.ingested} loads`);
      await refreshStatus();
    });
  }

  async function handleDisconnect() {
    await runAction("disconnect", async () => {
      const nextStatus = await disconnectDat();
      setStatus(nextStatus);
      setLastSync(null);
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
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
              disabled={busyAction !== null || !status?.connected}
              type="button"
              onClick={handleTest}
            >
              <TestTube2 className="h-4 w-4" />
              {busyAction === "test" ? "Testing..." : "Test"}
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
              disabled={busyAction !== null || !status?.connected}
              type="button"
              onClick={handleSync}
            >
              <RefreshCw className="h-4 w-4" />
              {busyAction === "sync" ? "Syncing..." : "Sync now"}
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-60"
              disabled={busyAction !== null || !status?.connected}
              type="button"
              onClick={handleDisconnect}
            >
              <Trash2 className="h-4 w-4" />
              Disconnect
            </button>
          </div>
        </form>

        <div className="mt-5 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
          <div>
            <span className="block font-medium text-slate-900">Last sync</span>
            {formatDate(status?.last_sync_at)}
          </div>
          <div>
            <span className="block font-medium text-slate-900">Last error</span>
            {status?.last_error || "None"}
          </div>
          <div>
            <span className="block font-medium text-slate-900">Last run</span>
            {lastSync
              ? `${lastSync.fetched} fetched, ${lastSync.ingested} ingested`
              : "No manual run yet"}
          </div>
        </div>

        {message ? <p className="mt-4 text-sm font-medium text-green-700">{message}</p> : null}
        {error ? <p className="mt-4 text-sm font-medium text-red-700">{error}</p> : null}
      </section>
    </main>
  );
}
