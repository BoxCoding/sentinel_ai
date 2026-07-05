"use client";
import { useEffect, useState } from "react";
import { Box, Chip, CircularProgress, Stack, Typography } from "@mui/material";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

function eventMeta(e: any): { label: string; color: "error" | "warning" | "info" | "success"; text: string } {
  if (e.channel) return { label: "NOTIFY", color: "info", text: `${e.channel} → ${e.recipient}: ${e.subject}` };
  if (e.priority) return { label: e.priority, color: e.priority.startsWith("P1") ? "error" : "warning", text: e.summary ?? "" };
  return { label: (e.type ?? e.emergency_type ?? "incident").toUpperCase(), color: "error",
           text: e.description ?? e.summary ?? "" };
}

export default function TimelinePage() {
  const [events, setEvents] = useState<any[] | null>(null);

  useEffect(() => {
    api.get("/dashboard/timeline").then(setEvents).catch(() => setEvents([]));
  }, []);

  if (events === null) return <AppShell><CircularProgress /></AppShell>;

  return (
    <AppShell>
      <Typography variant="h5" sx={{ mb: 2 }}>Incident Timeline</Typography>
      {events.length === 0 && (
        <Typography color="text.secondary">
          No events yet — run a decision cycle or report an incident.
        </Typography>
      )}
      <Stack spacing={0}>
        {events.map((e, i) => {
          const meta = eventMeta(e);
          return (
            <Stack key={e.id ?? i} direction="row" spacing={2}>
              <Stack alignItems="center">
                <Box sx={{ width: 12, height: 12, borderRadius: "50%", bgcolor: `${meta.color}.main`, mt: 0.75 }} />
                {i < events.length - 1 && <Box sx={{ width: 2, flex: 1, bgcolor: "#E2E8F0" }} />}
              </Stack>
              <Box sx={{ pb: 3 }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip size="small" label={meta.label} color={meta.color} />
                  <Typography variant="caption" color="text.secondary">
                    {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
                  </Typography>
                </Stack>
                <Typography variant="body2" sx={{ mt: 0.5 }}>{meta.text}</Typography>
              </Box>
            </Stack>
          );
        })}
      </Stack>
    </AppShell>
  );
}
