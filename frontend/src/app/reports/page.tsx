"use client";
import { useEffect, useState } from "react";
import {
  Card, CardContent, Chip, CircularProgress, Stack, Typography,
} from "@mui/material";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default function ReportsPage() {
  const [decisions, setDecisions] = useState<any[] | null>(null);

  useEffect(() => {
    api.get("/decisions").then(setDecisions).catch(() => setDecisions([]));
  }, []);

  if (decisions === null) return <AppShell><CircularProgress /></AppShell>;

  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Decision Reports</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Every AI decision includes risk score, confidence, reasoning and estimated impact
        (full executive KPIs live in Looker Studio — see docs/looker.md).
      </Typography>
      {decisions.length === 0 && (
        <Typography color="text.secondary">No decisions yet — run a decision cycle.</Typography>
      )}
      <Stack spacing={2}>
        {decisions.map((d) => (
          <Card key={d.id}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Chip label={d.priority} color={d.priority?.startsWith("P1") ? "error" : "warning"} size="small" />
                <Chip label={`Risk ${Math.round((d.risk_score ?? 0) * 100)}%`} size="small" variant="outlined" />
                <Chip label={`Confidence ${Math.round((d.confidence ?? 0) * 100)}%`} size="small" variant="outlined" />
                <Typography variant="caption" color="text.secondary" sx={{ ml: "auto" }}>
                  {d.created_at ? new Date(d.created_at).toLocaleString() : ""}
                </Typography>
              </Stack>
              <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", mb: 1 }}>{d.reasoning}</Typography>
              <Typography variant="caption" color="warning.main">
                Estimated impact: {d.estimated_impact}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </AppShell>
  );
}
