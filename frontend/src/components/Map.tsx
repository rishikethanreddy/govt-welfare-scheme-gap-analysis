"use client"
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icon in Leaflet + React
const icon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

export default function InteractiveMap({ data }: { data: any[] }) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return <div className="h-96 w-full bg-gray-100 animate-pulse rounded-md flex items-center justify-center">Loading Map...</div>;

  // Center of India roughly
  const center: [number, number] = [20.5937, 78.9629];

  return (
    <div className="h-[500px] w-full rounded-md overflow-hidden shadow-sm border border-gray-200">
      <MapContainer center={center} zoom={4} scrollWheelZoom={false} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {/* We would map through geographic data to render specific state polygons or markers here */}
        <Marker position={[28.6139, 77.2090]} icon={icon}>
          <Popup>
            Delhi <br /> High awareness gap signals detected.
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
