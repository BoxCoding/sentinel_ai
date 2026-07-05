"use client";
import { useCallback, useEffect, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  LinearProgress, Stack, Typography,
} from "@mui/material";
import MyLocationIcon from "@mui/icons-material/MyLocation";
import TipsAndUpdatesIcon from "@mui/icons-material/TipsAndUpdates";
import AppShell from "@/components/AppShell";
import RiskGauge from "@/components/RiskGauge";
import { api } from "@/lib/api";

type Briefing = {
  district: string;
  city: string;
  distance_km: number;
  weather: { temp_c: number; humidity: number; wind_kmh: number; rain_6h_mm: number; river_level_m: number };
  risks: { flood: number; fire: number; accident: number; flood_explanation: string };
  nearest_hospitals: { hospital: string; occupancy: number; icu_beds_free: number; distance_km: number }[];
  ai_summary: string;
  suggestions: string[];
};

const FALLBACK_CITIES = [
  { label: "Delhi", lat: 28.6139, lng: 77.209 },
  { label: "Gurugram", lat: 28.4595, lng: 77.0266 },
  { label: "Mumbai", lat: 19.076, lng: 72.8777 },
  { label: "Bengaluru", lat: 12.9716, lng: 77.5946 },
];

export default function LocationPage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [status, setStatus] = useState<"locating" | "denied" | "loading" | "ready" | "error">("locating");

  const load = useCallback(async (lat: number, lng: number) => {
    setStatus("loading");
    try {
      setBriefing(await api.post("/location/briefing", { lat, lng }));
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) { setStatus("denied"); return; }
    navigator.geolocation.getCurrentPosition(
      (pos) => load(pos.coords.latitude, pos.coords.longitude),
      () => setStatus("denied"),
      { timeout: 8000 },
    );
  }, [load]);

  return (
    <AppShell>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
        <MyLocationIcon color="primary" />
        <Typography variant="h5">My Location — AI Briefing</Typography>
      </Stack>

      {(status === "locating" || status === "loading") && <CircularProgress />}

      {status === "denied" && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Location access unavailable — pick a city instead:
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            {FALLBACK_CITIES.map((c) => (
              <Button key={c.label} size="small" variant="outlined"
                      onClick={() => load(c.lat, c.lng)}>{c.label}</Button>
            ))}
          </Stack>
        </Alert>
      )}

      {status === "error" && <Alert severity="error">Could not load briefing. Is the backend running?</Alert>}

      {status === "ready" && briefing && (
        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Chip color="primary" label={briefing.district} />
                <Chip variant="outlined" label={briefing.city} />
                <Typography variant="caption" color="text.secondary">
                  nearest sensor {briefing.distance_km} km away
                </Typography>
              </Stack>
              <Typography variant="body1" sx={{ mb: 1 }}>{briefing.ai_summary}</Typography>
              <Typography variant="body2" color="text.secondary">
                {briefing.weather.temp_c}°C · humidity {Math.round(briefing.weather.humidity * 100)}% ·
                wind {briefing.weather.wind_kmh} km/h · rain {briefing.weather.rain_6h_mm}mm/6h ·
                river {briefing.weather.river_level_m}m
              </Typography>
            </CardContent>
          </Card>

          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <Card sx={{ flex: 1 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Risks Near You</Typography>
                <Stack direction="row" justifyContent="space-around">
                  <RiskGauge value={briefing.risks.flood} label="Flood" />
                  <RiskGauge value={briefing.risks.fire} label="Fire" />
                  <RiskGauge value={briefing.risks.accident} label="Accident" />
                </Stack>
                <Typography variant="caption" color="text.secondary">
                  {briefing.risks.flood_explanation}
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ flex: 1 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Nearest Hospitals</Typography>
                <Stack spacing={1.5}>
                  {briefing.nearest_hospitals.map((h) => (
                    <Box key={h.hospital}>
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="body2">{h.hospital}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {h.distance_km} km · ICU free: {h.icu_beds_free}
                        </Typography>
                      </Stack>
                      <LinearProgress variant="determinate" value={h.occupancy * 100}
                                      color={h.occupancy > 0.9 ? "error" : h.occupancy > 0.8 ? "warning" : "success"}
                                      sx={{ height: 8, borderRadius: 4, mt: 0.5 }} />
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Stack>

          <Card>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <TipsAndUpdatesIcon color="warning" />
                <Typography variant="h6">AI Suggestions</Typography>
              </Stack>
              <Stack spacing={1}>
                {briefing.suggestions.map((s, i) => (
                  <Alert key={i} severity={s.startsWith("HIGH") ? "error" : "warning"}
                         icon={false} sx={{ py: 0.25 }}>
                    {s}
                  </Alert>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}
    </AppShell>
  );
}
