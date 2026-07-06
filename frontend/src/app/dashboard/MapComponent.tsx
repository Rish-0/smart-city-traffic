'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface Intersection {
  intersection_id: string;
  zone: string;
  latitude: number | null;
  longitude: number | null;
  current_volume: number;
  congestion_level: string;
  avg_speed: number;
}

const CONGESTION_COLORS: Record<string, string> = {
  Low: '#06d6a0', Moderate: '#f59e0b', High: '#f97316', Critical: '#ef4444'
};

export default function MapComponent({ intersections }: { intersections: Intersection[] }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;

    const map = L.map(mapRef.current, {
      center: [44.975, -93.265],
      zoom: 13,
      zoomControl: true,
      attributionControl: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
    }).addTo(map);

    mapInstance.current = map;

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapInstance.current || !intersections.length) return;
    const map = mapInstance.current;

    // Clear existing markers
    map.eachLayer(layer => {
      if (layer instanceof L.CircleMarker) map.removeLayer(layer);
    });

    intersections.forEach(int => {
      if (!int.latitude || !int.longitude) return;
      const color = CONGESTION_COLORS[int.congestion_level] || '#8892a8';

      L.circleMarker([int.latitude, int.longitude], {
        radius: 10,
        fillColor: color,
        fillOpacity: 0.8,
        color: color,
        weight: 2,
        opacity: 1,
      })
        .bindPopup(`
          <div style="font-family: Inter, sans-serif; font-size: 13px; min-width: 160px;">
            <strong style="font-size: 15px;">${int.intersection_id}</strong><br/>
            <span style="color: #8892a8;">Zone:</span> ${int.zone}<br/>
            <span style="color: #8892a8;">Volume:</span> ${int.current_volume}<br/>
            <span style="color: #8892a8;">Speed:</span> ${int.avg_speed} km/h<br/>
            <span style="color: ${color}; font-weight: 600;">● ${int.congestion_level}</span>
          </div>
        `)
        .addTo(map);
    });
  }, [intersections]);

  return <div ref={mapRef} className="map-container" />;
}
