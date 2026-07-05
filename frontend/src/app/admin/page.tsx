"use client";
import { useEffect, useState } from "react";
import {
  Card, CardContent, CircularProgress, Stack, Tab, Tabs, Typography,
} from "@mui/material";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

const TABS = ["notifications", "work_orders", "incident_reports", "agent_runs"] as const;

export default function AdminPage() {
  const [audit, setAudit] = useState<Record<string, any[]> | null>(null);
  const [tab, setTab] = useState(0);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    api.get("/dashboard/admin/audit").then(setAudit).catch(() => setDenied(true));
  }, []);

  if (denied) {
    return (
      <AppShell>
        <Typography variant="h6" color="error">Admin role required.</Typography>
      </AppShell>
    );
  }
  if (!audit) return <AppShell><CircularProgress /></AppShell>;

  const rows = audit[TABS[tab]] ?? [];
  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Admin — Audit Trail</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        {TABS.map((t) => <Tab key={t} label={`${t.replace("_", " ")} (${(audit[t] ?? []).length})`} />)}
      </Tabs>
      <Stack spacing={1}>
        {rows.map((r, i) => (
          <Card key={r.id ?? i}>
            <CardContent sx={{ py: 1.5 }}>
              <Typography variant="caption" color="text.secondary">
                {r.created_at ? new Date(r.created_at).toLocaleString() : ""}
              </Typography>
              <Typography variant="body2" component="pre" sx={{
                whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 12, m: 0,
              }}>
                {JSON.stringify(r, null, 2).slice(0, 600)}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </AppShell>
  );
}
