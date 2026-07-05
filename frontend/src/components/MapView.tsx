"use client";
/* Real map, no API key required: Leaflet + OpenStreetMap tiles by default,
   upgraded to Google Maps automatically when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
   is set. Bounds auto-fit the visible markers, so the same component works
   citywide (Gurugram) or nationwide (Delhi NCR + Mumbai + Bengaluru). */
import { useEffect, useRef } from "react";
import { Box, Chip, Stack } from "@mui/material";
import "leaflet/dist/leaflet.css";

export type MapMarker = {
  lat: number;
  lng: number;
  label: string;
  kind: "incident" | "hospital" | "closure" | "flood";
  city?: string;
};

const KIND_COLOR: Record<MapMarker["kind"], string> = {
  incident: "#DC2626",
  hospital: "#059669",
  closure: "#D97706",
  flood: "#06B6D4",
};

const MAPS_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

function GoogleMapView({ markers }: { markers: MapMarker[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = "gmaps-script";
    const init = () => {
      const g = (window as any).google;
      if (!ref.current || !g || markers.length === 0) return;
      const map = new g.maps.Map(ref.current, { mapTypeId: "roadmap" });
      const b = new g.maps.LatLngBounds();
      markers.forEach((m) => {
        b.extend({ lat: m.lat, lng: m.lng });
        new g.maps.Marker({
          position: { lat: m.lat, lng: m.lng },
          map,
          title: m.label,
          icon: {
            path: g.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: KIND_COLOR[m.kind],
            fillOpacity: 0.9,
            strokeWeight: 1.5,
            strokeColor: "#fff",
          },
        });
      });
      map.fitBounds(b);
    };
    if (document.getElementById(id)) { init(); return; }
    const script = document.createElement("script");
    script.id = id;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${MAPS_KEY}`;
    script.onload = init;
    document.head.appendChild(script);
  }, [markers]);

  return <div ref={ref} style={{ width: "100%", height: 560, borderRadius: 12 }} />;
}

function LeafletMapView({ markers }: { markers: MapMarker[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !ref.current) return;

      if (!mapRef.current) {
        mapRef.current = L.map(ref.current, { scrollWheelZoom: true })
          .setView([22.5, 77.5], 5);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 18,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(mapRef.current);
        layerRef.current = L.layerGroup().addTo(mapRef.current);
      }

      layerRef.current.clearLayers();
      if (markers.length === 0) return;
      const bounds = L.latLngBounds(markers.map((m) => [m.lat, m.lng] as [number, number]));
      markers.forEach((m) => {
        L.circleMarker([m.lat, m.lng], {
          radius: 9,
          color: "#ffffff",
          weight: 2,
          fillColor: KIND_COLOR[m.kind],
          fillOpacity: 0.95,
        })
          .bindPopup(`<b>${m.kind.toUpperCase()}</b><br/>${m.label}`)
          .bindTooltip(m.label)
          .addTo(layerRef.current);
      });
      mapRef.current.fitBounds(bounds.pad(0.15));
    })();
    return () => { cancelled = true; };
  }, [markers]);

  useEffect(() => () => { mapRef.current?.remove(); mapRef.current = null; }, []);

  return (
    <Box ref={ref}
         sx={{ width: "100%", height: 560, borderRadius: 3, overflow: "hidden",
               border: "1px solid #E2E8F0", zIndex: 0,
               "& .leaflet-container": { height: "100%", width: "100%" } }} />
  );
}

export default function MapView({ markers }: { markers: MapMarker[] }) {
  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 1.5 }}>
        {Object.entries(KIND_COLOR).map(([kind, color]) => (
          <Chip key={kind} size="small" label={kind}
                sx={{ bgcolor: "transparent", border: `1px solid ${color}`, color }} />
        ))}
      </Stack>
      {MAPS_KEY ? <GoogleMapView markers={markers} /> : <LeafletMapView markers={markers} />}
    </Box>
  );
}
