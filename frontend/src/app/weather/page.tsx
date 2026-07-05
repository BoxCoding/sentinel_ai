"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CircularProgress, Stack, Typography } from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default function WeatherPage() {
  const [rows, setRows] = useState<any[] | null>(null);

  useEffect(() => {
    api.get("/dashboard/weather").then(setRows).catch(() => setRows([]));
  }, []);

  if (rows === null) return <AppShell><CircularProgress /></AppShell>;

  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Weather Dashboard</Typography>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>6-hour Rainfall by District (mm)</Typography>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={rows}>
              <XAxis dataKey="district" tick={{ fill: "#64748B", fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={70} />
              <YAxis tick={{ fill: "#64748B" }} />
              <Tooltip contentStyle={{ background: "#FFFFFF", border: "1px solid #E2E8F0" }} />
              <ReferenceLine y={80} stroke="#DC2626" strokeDasharray="4 4"
                             label={{ value: "Level-2 alert", fill: "#DC2626", fontSize: 11 }} />
              <Bar dataKey="rain_6h_mm" fill="#0D9488" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }} useFlexGap>
        {rows.map((w) => (
          <Card key={w.district} sx={{ minWidth: 210, flex: 1 }}>
            <CardContent>
              <Typography variant="subtitle1">{w.district}</Typography>
              <Typography variant="body2" color="text.secondary">
                {w.temp_c}°C · humidity {Math.round(w.humidity * 100)}% · wind {w.wind_kmh} km/h
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}
                          color={w.river_level_m > 4 ? "error.main" : "text.secondary"}>
                River {w.river_level_m}m {w.river_level_m > 4 ? "⚠ near danger mark (4.5m)" : ""}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </AppShell>
  );
}
