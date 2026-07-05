"use client";
import { useEffect, useRef, useState } from "react";
import {
  Alert, Box, Chip, CircularProgress, IconButton, Paper, Stack, TextField, Typography,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

type Msg = {
  from: "user" | "ai";
  text: string;
  mode?: string;
  citations?: { source: string; excerpt: string }[];
  actionPlan?: { source_agent: string; action: string }[];
};

const SUGGESTIONS = [
  "Which hospitals should receive additional ambulances?",
  "What is the flood SOP activation protocol?",
  "Summarize today's emergencies",
  "Recommend a deployment plan",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [ai, setAi] = useState<{ connected: boolean; model: string } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get("/dashboard/summary").then((s) => setAi(s.ai ?? null)).catch(() => {});
  }, []);

  const send = async (text: string) => {
    if (!text.trim() || busy) return;
    setMessages((m) => [...m, { from: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const r = await api.post("/chat", { message: text });
      setMessages((m) => [...m, {
        from: "ai", text: r.answer, mode: r.mode,
        citations: r.citations, actionPlan: r.action_plan,
      }]);
    } catch (e) {
      setMessages((m) => [...m, { from: "ai", text: "Request failed. Is the backend running?" }]);
    } finally {
      setBusy(false);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <AppShell>
      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h5">AI Chat — Gemini-powered Assistant</Typography>
        {ai && (
          <Chip size="small" color={ai.connected ? "success" : "warning"}
                label={ai.connected ? ai.model : "offline demo"} />
        )}
      </Stack>
      {ai && !ai.connected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Gemini is not connected — responses are canned demo text. Set
          GEMINI_API_KEY in backend/.env and restart the backend.
        </Alert>
      )}
      <Paper variant="outlined"
             sx={{ height: "calc(100vh - 260px)", p: 2, overflowY: "auto", bgcolor: "#FFFFFF" }}>
        {messages.length === 0 && (
          <Stack spacing={1} alignItems="flex-start">
            <Typography color="text.secondary" sx={{ mb: 1 }}>Try:</Typography>
            {SUGGESTIONS.map((s) => (
              <Chip key={s} label={s} onClick={() => send(s)} variant="outlined" />
            ))}
          </Stack>
        )}
        <Stack spacing={2}>
          {messages.map((m, i) => (
            <Box key={i} sx={{
              alignSelf: m.from === "user" ? "flex-end" : "flex-start",
              maxWidth: "75%", p: 1.5, borderRadius: 3,
              bgcolor: m.from === "user" ? "primary.main" : "#F0FDFA",
              color: m.from === "user" ? "#FFFFFF" : "text.primary",
            }}>
              {m.mode && <Chip size="small" label={m.mode.toUpperCase()} sx={{ mb: 1 }}
                               color={m.mode === "decision" ? "error" : "info"} />}
              <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{m.text}</Typography>
              {m.actionPlan && m.actionPlan.length > 0 && (
                <Stack spacing={0.5} sx={{ mt: 1 }}>
                  {m.actionPlan.slice(0, 5).map((a, j) => (
                    <Typography key={j} variant="caption" color="warning.main">
                      → [{a.source_agent}] {a.action}
                    </Typography>
                  ))}
                </Stack>
              )}
              {m.citations && m.citations.length > 0 && (
                <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: "wrap" }}>
                  {m.citations.map((c, j) => (
                    <Chip key={j} size="small" label={c.source} variant="outlined" title={c.excerpt} />
                  ))}
                </Stack>
              )}
            </Box>
          ))}
          {busy && <CircularProgress size={24} />}
          <div ref={bottomRef} />
        </Stack>
      </Paper>
      <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
        <TextField fullWidth size="small" placeholder="Ask about risks, SOPs, or request a deployment plan…"
                   value={input} onChange={(e) => setInput(e.target.value)}
                   onKeyDown={(e) => e.key === "Enter" && send(input)} />
        <IconButton color="primary" onClick={() => send(input)} aria-label="Send"><SendIcon /></IconButton>
      </Stack>
    </AppShell>
  );
}
