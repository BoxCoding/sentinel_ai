"use client";
import { useEffect, useState } from "react";
import {
  Card, CardContent, Chip, CircularProgress, LinearProgress, Stack, Typography,
} from "@mui/material";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default function TrafficPage() {
  const [data, setData] = useState<{ sensors: any[]; closures: any[] } | null>(null);

  useEffect(() => {
    api.get("/dashboard/traffic").then(setData).catch(() => setData({ sensors: [], closures: [] }));
  }, []);

  if (!data) return <AppShell><CircularProgress /></AppShell>;

  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Traffic Dashboard</Typography>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Card sx={{ flex: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Live Congestion</Typography>
            <Stack spacing={1.5}>
              {data.sensors
                .sort((a, b) => b.congestion_index - a.congestion_index)
                .map((s) => (
                  <Stack key={s.road} direction="row" spacing={2} alignItems="center">
                    <Typography variant="body2" sx={{ width: 180 }}>{s.road}</Typography>
                    <LinearProgress variant="determinate" value={s.congestion_index * 100}
                                    color={s.congestion_index > 0.75 ? "error" : s.congestion_index > 0.5 ? "warning" : "success"}
                                    sx={{ flex: 1, height: 10, borderRadius: 5 }} />
                    <Typography variant="caption" sx={{ width: 90 }} color="text.secondary">
                      {s.avg_speed_kmh} km/h
                    </Typography>
                  </Stack>
                ))}
            </Stack>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Road Closures</Typography>
            <Stack spacing={1.5}>
              {data.closures.length === 0 && <Typography color="text.secondary">No closures.</Typography>}
              {data.closures.map((c) => (
                <Stack key={c.road} spacing={0.5}>
                  <Stack direction="row" spacing={1}>
                    <Chip size="small" color="warning" label="CLOSED" />
                    <Typography variant="body2">{c.road}</Typography>
                  </Stack>
                  <Typography variant="caption" color="text.secondary">{c.reason}</Typography>
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </AppShell>
  );
}
