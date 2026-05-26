"use client";

import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

type TruckPosition = {
  truck_id: string;
  status: string;
  latitude: number | null;
  longitude: number | null;
  speed: number | null;
  current_location: string | null;
};

type Props = {
  trucks: TruckPosition[];
};

export default function LiveFleetMap({ trucks }: Props) {
  const visibleTrucks = trucks.filter(
    (truck) =>
      truck.latitude !== null &&
      truck.longitude !== null
  );

  return (
    <div className="h-[700px] w-full overflow-hidden rounded-2xl border">
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

        {visibleTrucks.map((truck) => (
          <Marker
            key={truck.truck_id}
            position={[
              truck.latitude as number,
              truck.longitude as number,
            ]}
          >
            <Popup>
              <div className="space-y-1">
                <div className="font-semibold">
                  {truck.truck_id}
                </div>

                <div>Status: {truck.status}</div>

                <div>
                  Speed: {truck.speed ?? "-"} mph
                </div>

                <div>
                  {truck.current_location ?? "Unknown"}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
