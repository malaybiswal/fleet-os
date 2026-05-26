"use client";

import { useEffect } from "react";

import L from "leaflet";
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

type TruckPosition = {
  truck_id: string;
  status: string;
  latitude: number | null;
  longitude: number | null;
  speed: number | null;
  current_location: string | null;
  last_seen_at?: string | null;
};

type Props = {
  trucks: TruckPosition[];
};

function getTruckColor(status: string): string {
  switch (status.toLowerCase()) {
    case "active":
      return "#16a34a";

    case "idle":
      return "#2563eb";

    case "maintenance":
      return "#dc2626";

    default:
      return "#f59e0b";
  }
}

function createTruckIcon(
  status: string,
  truckId: string,
) {
  const color = getTruckColor(status);

  return L.divIcon({
    className: "",
    html: `
      <div style="
        display:flex;
        align-items:center;
        gap:6px;
        white-space:nowrap;
      ">
        <div style="
          display:flex;
          align-items:center;
          justify-content:center;
          width:34px;
          height:34px;
          border-radius:10px;
          background:${color};
          color:white;
          border:3px solid white;
          box-shadow:0 4px 10px rgba(0,0,0,0.35);
          font-size:18px;
          line-height:1;
        ">
          🚚
        </div>

        <div style="
          background:white;
          padding:2px 6px;
          border-radius:6px;
          font-size:12px;
          font-weight:600;
          color:#0f172a;
          box-shadow:0 2px 6px rgba(0,0,0,0.15);
        ">
          ${truckId}
        </div>
      </div>
    `,
    iconSize: [90, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
}

function FitBounds({
  trucks,
}: {
  trucks: TruckPosition[];
}) {
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

export default function LiveFleetMap({
  trucks,
}: Props) {
  const visibleTrucks = trucks.filter(
    (truck) =>
      truck.latitude !== null &&
      truck.longitude !== null,
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
          <Marker
            key={truck.truck_id}
            position={[
              truck.latitude as number,
              truck.longitude as number,
            ]}
            icon={createTruckIcon(
              truck.status,
              truck.truck_id,
            )}
          >
            <Popup>
              <div className="space-y-1 text-sm">
                <div className="font-semibold">
                  {truck.truck_id}
                </div>

                <div>
                  Status:{" "}
                  <span className="font-medium">
                    {truck.status}
                  </span>
                </div>

                <div>
                  Speed: {truck.speed ?? "-"} mph
                </div>

                <div>
                  {truck.current_location ?? "Unknown"}
                </div>

                <div className="text-xs text-slate-500">
                  Last ping:{" "}
                  {truck.last_seen_at
                    ? new Date(
                        truck.last_seen_at,
                      ).toLocaleTimeString()
                    : "N/A"}
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
            Active
          </div>

          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-blue-600" />
            Idle
          </div>

          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-red-600" />
            Maintenance
          </div>
        </div>
      </div>
    </div>
  );
}