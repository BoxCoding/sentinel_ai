"use client";
import { Box, Typography } from "@mui/material";

export default function RiskGauge({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  const color = value > 0.75 ? "#DC2626" : value > 0.5 ? "#D97706" : "#059669";
  const angle = value * 270 - 135;
  return (
    <Box sx={{ textAlign: "center", p: 2 }}>
      <Box sx={{ position: "relative", width: 140, height: 140, mx: "auto" }}>
        <svg viewBox="0 0 100 100" width="140" height="140">
          <circle cx="50" cy="50" r="42" fill="none" stroke="#E5E9F2" strokeWidth="9"
                  strokeDasharray="198 264" strokeLinecap="round"
                  transform="rotate(135 50 50)" />
          <circle cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="9"
                  strokeDasharray={`${value * 198} 264`} strokeLinecap="round"
                  transform="rotate(135 50 50)" />
          <line x1="50" y1="50" x2="50" y2="18" stroke={color} strokeWidth="2.5"
                strokeLinecap="round" transform={`rotate(${angle} 50 50)`} />
        </svg>
        <Typography variant="h5" sx={{
          position: "absolute", top: "58%", left: "50%",
          transform: "translate(-50%, -50%)", color, fontWeight: 700,
        }}>
          {pct}%
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
    </Box>
  );
}
