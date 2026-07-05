"use client";
import { useEffect, useState } from "react";
import {
  Card, CardContent, Chip, CircularProgress, LinearProgress, Stack, Typography,
} from "@mui/material";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default function HospitalsPage() {
  const [rows, setRows] = useState<any[] | null>(null);
  const [forecast, setForecast] = useState<Record<string, any[]>>({});

  useEffect(() => {
    api.get("/dashboard/hospitals").then(setRows).catch(() => setRows([]));
    api.get("/predictions/hospital-occupancy?days=7").then(setForecast).catch(() => {});
  }, []);

  if (rows === null) return <AppShell><CircularProgress /></AppShell>;

  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Hospital Dashboard</Typography>
      <Stack spacing={2}>
        {rows.map((h) => (
          <Card key={h.hospital}>
            <CardContent>
              <Stack direction={{ xs: "column", md: "row" }} spacing={3} alignItems="center">
                <Stack sx={{ minWidth: 260 }} spacing={1}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="h6">{h.hospital}</Typography>
                    {h.occupancy > 0.9 && <Chip size="small" color="error" label="SURGE" />}
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {h.district} · {h.total_beds} beds · {h.doctors_on_duty} doctors ·
                    ICU free: {h.icu_beds_free} · Ambulances: {h.ambulances_available} ·
                    Medicine: {h.medicine_stock_days}d
                  </Typography>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <LinearProgress variant="determinate" value={h.occupancy * 100}
                                    color={h.occupancy > 0.9 ? "error" : h.occupancy > 0.8 ? "warning" : "success"}
                                    sx={{ flex: 1, height: 10, borderRadius: 5 }} />
                    <Typography variant="body2">{Math.round(h.occupancy * 100)}%</Typography>
                  </Stack>
                </Stack>
                <ResponsiveContainer width="100%" height={110}>
                  <LineChart data={forecast[h.hospital] ?? []}>
                    <XAxis dataKey="date" hide />
                    <YAxis domain={[0.4, 1]} hide />
                    <Tooltip contentStyle={{ background: "#FFFFFF", border: "1px solid #E2E8F0" }}
                             formatter={(v: number) => `${Math.round(v * 100)}%`} />
                    <ReferenceLine y={0.9} stroke="#DC2626" strokeDasharray="4 4" />
                    <Line type="monotone" dataKey="predicted_occupancy" stroke="#0D9488" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </AppShell>
  );
}
