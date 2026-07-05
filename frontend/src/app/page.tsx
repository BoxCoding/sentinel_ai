"use client";
import { useEffect, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Stack, Typography,
} from "@mui/material";
import BoltIcon from "@mui/icons-material/Bolt";
import AppShell from "@/components/AppShell";
import KpiCard from "@/components/KpiCard";
import RiskGauge from "@/components/RiskGauge";
import { api } from "@/lib/api";

type Summary = {
  ai?: { connected: boolean; model: string };
  weather_source?: string;
  open_incidents: number;
  total_incidents_today: number;
  active_calls: number;
  avg_hospital_occupancy: number | null;
  latest_risk_score: number | null;
  latest_priority: string | null;
  recent_decisions: { id: string; priority?: string; summary?: string; risk_score?: number }[];
};

export default function HomePage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.get("/dashboard/summary").then(setSummary).catch(() => {});
  useEffect(() => { load(); }, []);

  const runCycle = async () => {
    setRunning(true);
    setError("");
    try {
      await api.post("/agents/decision-cycle");
      await load();
    } catch {
      setError("Decision cycle failed — check that the backend is running on :8000.");
    } finally {
      setRunning(false);
    }
  };

  if (!summary) return <AppShell><CircularProgress /></AppShell>;

  return (
    <AppShell>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="h5">City Operations Overview</Typography>
        <Button variant="contained" startIcon={running ? <CircularProgress size={18} color="inherit" /> : <BoltIcon />}
                onClick={runCycle} disabled={running}>
          Run Decision Cycle
        </Button>
      </Stack>

      <Stack direction="row" spacing={1} sx={{ mb: 2.5 }}>
        <Chip size="small" variant="outlined"
              color={summary.weather_source === "open-meteo-live" ? "success" : "default"}
              label={summary.weather_source === "open-meteo-live"
                ? "Weather: LIVE (Open-Meteo)" : "Weather: synthetic demo"} />
        <Chip size="small" variant="outlined"
              color={summary.ai?.connected ? "success" : "warning"}
              label={summary.ai?.connected
                ? `AI: ${summary.ai.model} connected` : "AI: offline demo mode"} />
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>{error}</Alert>}

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 3 }}>
        <KpiCard label="Open Incidents" value={summary.open_incidents} color="#DC2626" />
        <KpiCard label="Active Emergency Calls" value={summary.active_calls} color="#D97706" />
        <KpiCard label="Avg Hospital Occupancy"
                 value={summary.avg_hospital_occupancy != null
                   ? `${Math.round(summary.avg_hospital_occupancy * 100)}%` : "—"}
                 color="#0D9488" />
        <KpiCard label="Incidents Today" value={summary.total_incidents_today} color="#059669" />
      </Stack>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Card sx={{ minWidth: 260 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Composite City Risk</Typography>
            <RiskGauge value={summary.latest_risk_score ?? 0}
                       label={summary.latest_priority ?? "No cycle run yet"} />
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Recent AI Decisions</Typography>
            {summary.recent_decisions.length === 0 && (
              <Typography color="text.secondary">
                Run a decision cycle to generate the first fused assessment.
              </Typography>
            )}
            <Stack spacing={1.5}>
              {summary.recent_decisions.map((d) => (
                <Box key={d.id} sx={{ p: 1.5, borderRadius: 2, bgcolor: "#F1F5F9" }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Chip size="small" label={d.priority ?? "P?"}
                          color={d.priority?.startsWith("P1") ? "error" : "warning"} />
                    <Typography variant="body2">{d.summary}</Typography>
                  </Stack>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </AppShell>
  );
}
