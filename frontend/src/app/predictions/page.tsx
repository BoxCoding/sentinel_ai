"use client";
import { useState } from "react";
import {
  Box, Button, Card, CardContent, CircularProgress, Slider, Stack, Typography,
} from "@mui/material";
import AppShell from "@/components/AppShell";
import RiskGauge from "@/components/RiskGauge";
import { api } from "@/lib/api";

type Explanation = {
  narrative: string;
  top_factors: { feature: string; value: number; attribution: number }[];
};

export default function PredictionsPage() {
  const [rain, setRain] = useState(60);
  const [river, setRiver] = useState(3.5);
  const [soil, setSoil] = useState(0.7);
  const [result, setResult] = useState<{ p: number; explanation: Explanation } | null>(null);
  const [loading, setLoading] = useState(false);

  const predict = async () => {
    setLoading(true);
    try {
      const r = await api.post("/predictions/flood", {
        rain_6h_mm: rain, river_level_m: river, soil_saturation: soil,
        drainage_capacity: 40, elevation_m: 15,
      });
      setResult({ p: r.flood_probability, explanation: r.explanation });
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Predictive Analytics — Flood Risk (What-If)</Typography>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Scenario Inputs</Typography>
            <Box sx={{ px: 1 }}>
              <Typography variant="body2">Rainfall last 6h: {rain} mm</Typography>
              <Slider value={rain} min={0} max={150} onChange={(_, v) => setRain(v as number)} />
              <Typography variant="body2">River level: {river.toFixed(1)} m (danger 4.5m)</Typography>
              <Slider value={river} min={1} max={6} step={0.1} onChange={(_, v) => setRiver(v as number)} />
              <Typography variant="body2">Soil saturation: {Math.round(soil * 100)}%</Typography>
              <Slider value={soil} min={0} max={1} step={0.05} onChange={(_, v) => setSoil(v as number)} />
            </Box>
            <Button variant="contained" onClick={predict} disabled={loading} sx={{ mt: 2 }}>
              {loading ? <CircularProgress size={20} /> : "Predict"}
            </Button>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Prediction + Explanation (XAI)</Typography>
            {result ? (
              <>
                <RiskGauge value={result.p} label="Flood probability" />
                <Typography variant="body2" sx={{ mb: 2 }}>{result.explanation.narrative}</Typography>
                <Stack spacing={1}>
                  {result.explanation.top_factors.map((f) => (
                    <Box key={f.feature} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Typography variant="caption" sx={{ width: 140 }}>{f.feature}</Typography>
                      <Box sx={{
                        height: 10, borderRadius: 5,
                        width: `${Math.min(Math.abs(f.attribution) * 300, 200)}px`,
                        bgcolor: f.attribution > 0 ? "#ff5d5d" : "#39d98a",
                      }} />
                      <Typography variant="caption" color="text.secondary">
                        {f.attribution > 0 ? "+" : ""}{f.attribution.toFixed(3)}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </>
            ) : (
              <Typography color="text.secondary">Adjust the scenario and press Predict.</Typography>
            )}
          </CardContent>
        </Card>
      </Stack>
    </AppShell>
  );
}
