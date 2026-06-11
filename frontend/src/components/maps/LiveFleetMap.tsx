"use client";

import { useEffect } from "react";

import L from "leaflet";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import type { LiveTruckPosition } from "@/lib/api";

import "leaflet/dist/leaflet.css";

type Props = {
  trucks: LiveTruckPosition[];
};

function getTruckColor(status: string): string {
  switch (status.toLowerCase()) {
    case "moving":
    case "active":
      return "#16a34a";
    case "slow":
      return "#f59e0b";
    case "idle":
      return "#2563eb";
    case "stopped":
      return "#64748b";
    case "maintenance":
      return "#dc2626";
    default:
      return "#64748b";
  }
}

function formatStatus(status: string): string {
  return status.replaceAll("_", " ");
}

function formatAlertType(alertType: string): string {
  return alertType.replaceAll("_", " ");
}

function formatRelativeTime(timestamp?: string | null): string {
  if (!timestamp) return "N/A";

  const diffSeconds = Math.max(
    0,
    Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000),
  );

  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;

  return `${Math.floor(diffSeconds / 3600)}h ago`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function createTruckIcon(
  status: string,
  truckId: string,
  heading = 0,
  activeAlertCount = 0,
) {
  const color = getTruckColor(status);
  const normalizedStatus = status.toLowerCase();
  const isMoving =
    normalizedStatus === "moving" || normalizedStatus === "active";
  const hasActiveAlerts = activeAlertCount > 0;
  const safeTruckId = escapeHtml(truckId);

  return L.divIcon({
    className: "",
    html: `
      <style>
        @keyframes fleetPulse {
          0% { transform: scale(0.8); opacity: 0.35; }
          100% { transform: scale(1.6); opacity: 0; }
        }
        @keyframes alertPulse {
          0% { transform: scale(0.95); opacity: 0.55; }
          100% { transform: scale(1.9); opacity: 0; }
        }
      </style>

      <div style="display:flex;align-items:center;gap:6px;white-space:nowrap;">
        <div style="position:relative;">
          ${
            hasActiveAlerts
              ? `<div style="position:absolute;inset:-10px;border-radius:18px;background:#dc2626;opacity:0.32;animation:alertPulse 1.15s ease-out infinite;"></div>`
              : ""
          }

          ${
            isMoving && !hasActiveAlerts
              ? `<div style="position:absolute;inset:-6px;border-radius:14px;background:${color};opacity:0.22;animation:fleetPulse 1.6s ease-out infinite;"></div>`
              : ""
          }

          <div style="position:absolute;top:-12px;left:10px;color:${color};font-size:14px;line-height:1;transform:rotate(${heading}deg);transform-origin:center;transition:transform 0.4s ease;text-shadow:0 1px 2px rgba(255,255,255,0.9);">
            ▲
          </div>

          <div style="position:relative;display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;background:${color};color:white;border:3px solid ${hasActiveAlerts ? "#dc2626" : "white"};box-shadow:${hasActiveAlerts ? "0 0 0 4px rgba(220,38,38,0.22), 0 4px 12px rgba(127,29,29,0.45)" : "0 4px 10px rgba(0,0,0,0.35)"};font-size:18px;line-height:1;">
            🚚
          </div>

          ${
            hasActiveAlerts
              ? `<div style="position:absolute;right:-9px;top:-10px;display:flex;align-items:center;justify-content:center;min-width:20px;height:20px;border-radius:999px;background:#dc2626;color:white;border:2px solid white;font-size:11px;font-weight:800;line-height:1;box-shadow:0 2px 7px rgba(127,29,29,0.4);">${activeAlertCount}</div>`
              : ""
          }
        </div>

        <div style="background:white;padding:2px 6px;border-radius:6px;font-size:12px;font-weight:600;color:#0f172a;box-shadow:0 2px 6px rgba(0,0,0,0.15);">
          ${safeTruckId}
        </div>
      </div>
    `,
    iconSize: [100, 46],
    iconAnchor: [17, 28],
    popupAnchor: [0, -28],
  });
}

function FitBounds({ trucks }: { trucks: LiveTruckPosition[] }) {
  const map = useMap();

  useEffect(() => {
    if (trucks.length === 0) {
      return;
    }

    const bounds = L.latLngBounds(
      trucks.map((truck) => [
        truck.latitude as number,
        truck.longitude as number,
      ]),
    );

    map.fitBounds(bounds, {
      padding: [60, 60],
    });
  }, [map, trucks]);

  return null;
}

export default function LiveFleetMap({ trucks }: Props) {
  const visibleTrucks = trucks.filter(
    (truck) => truck.latitude !== null && truck.longitude !== null,
  );

  return (
    <div className="relative h-[700px] w-full overflow-hidden rounded-2xl border border-slate-200 shadow-sm">
      <MapContainer
        center={[31.0, -99.0]}
        zoom={5}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitBounds trucks={visibleTrucks} />

        {visibleTrucks.map((truck) => (
          <Polyline
            key={`route-${truck.truck_id}`}
            positions={[
              [
                (truck.latitude as number) - 0.4,
                (truck.longitude as number) - 0.4,
              ],
              [truck.latitude as number, truck.longitude as number],
            ]}
            pathOptions={{
              color: getTruckColor(truck.status),
              weight: 3,
              opacity: 0.35,
              dashArray: "8 8",
            }}
          />
        ))}

        {visibleTrucks.map((truck) => (
          <Marker
            key={truck.truck_id}
            position={[truck.latitude as number, truck.longitude as number]}
            icon={createTruckIcon(
              truck.status,
              truck.truck_id,
              truck.heading ?? 0,
              truck.active_alert_count,
            )}
          >
            <Popup>
              <div className="space-y-1 text-sm">
                <div className="font-semibold">{truck.truck_id}</div>
                <div>
                  Status:{" "}
                  <span className="font-medium">
                    {formatStatus(truck.status)}
                  </span>
                </div>
                <div>Speed: {truck.speed ?? "-"} mph</div>
                <div>Heading: {truck.heading ?? 0}°</div>
                <div>{truck.current_location ?? "Unknown"}</div>
                {truck.active_alert_count > 0 ? (
                  <div className="mt-2 rounded-md border border-red-100 bg-red-50 p-2">
                    <div className="text-xs font-semibold uppercase tracking-wide text-red-700">
                      {truck.active_alert_count} active{" "}
                      {truck.active_alert_count === 1 ? "alert" : "alerts"}
                    </div>
                    <div className="mt-1 space-y-1">
                      {truck.active_alerts.slice(0, 3).map((alert) => (
                        <div key={alert.id} className="text-xs text-red-900">
                          <span className="font-semibold capitalize">
                            {alert.severity}
                          </span>
                          {": "}
                          {formatAlertType(alert.alert_type)}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div className="text-xs text-slate-500">
                  Last ping: {formatRelativeTime(truck.last_seen_at)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      <div className="absolute bottom-4 right-4 z-[1000] rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
        <div className="mb-2 text-xs font-semibold text-slate-700">
          Fleet Status
        </div>

        <div className="space-y-1 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-green-600" />
            Moving
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-amber-500" />
            Slow
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-blue-600" />
            Idle
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-slate-500" />
            Stopped
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-red-600" />
            Maintenance
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full border-2 border-red-600 bg-white shadow-[0_0_0_3px_rgba(220,38,38,0.18)]" />
            Active alerts
          </div>
        </div>
      </div>
    </div>
  );
}
