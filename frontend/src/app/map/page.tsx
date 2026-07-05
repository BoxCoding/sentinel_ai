"use client";
import { useEffect, useMemo, useState } from "react";
import { Chip, CircularProgress, Stack, Typography } from "@mui/material";
import AppShell from "@/components/AppShell";
import MapView, { MapMarker } from "@/components/MapView";
import { api } from "@/lib/api";

const CITIES = ["All", "Delhi NCR", "Mumbai", "Bengaluru"];

export default function MapPage() {
  const [markers, setMarkers] = useState<MapMarker[] | null>(null);
  const [city, setCity] = useState("All");

  useEffect(() => {
    api.get("/dashboard/map").then((layers) => {
      const m: MapMarker[] = [];
      layers.incidents.forEach((i: any) =>
        i.lat && m.push({ lat: i.lat, lng: i.lng, kind: "incident", city: i.city,
                 label: `${i.type ?? i.emergency_type ?? "incident"}: ${i.description ?? i.summary ?? ""}` }));
      layers.hospitals.forEach((h: any) =>
        m.push({ lat: h.lat, lng: h.lng, kind: "hospital", city: h.city,
                 label: `${h.hospital} — ${Math.round(h.occupancy * 100)}% occupied, ${h.icu_beds_free} ICU free` }));
      layers.flood_zones.forEach((f: any) =>
        m.push({ lat: f.lat, lng: f.lng, kind: "flood", city: f.city,
                 label: `${f.district}: ${f.rain_6h_mm}mm rain / 6h` }));
      setMarkers(m);
    }).catch(() => setMarkers([]));
  }, []);

  const visible = useMemo(
    () => (markers ?? []).filter((m) => city === "All" || m.city === city || !m.city),
    [markers, city],
  );

  return (
    <AppShell>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h5">Emergency Map</Typography>
        <Stack direction="row" spacing={1}>
          {CITIES.map((c) => (
            <Chip key={c} label={c} color={city === c ? "primary" : "default"}
                  variant={city === c ? "filled" : "outlined"}
                  onClick={() => setCity(c)} />
          ))}
        </Stack>
      </Stack>
      {markers === null ? <CircularProgress /> : <MapView markers={visible} />}
    </AppShell>
  );
}
