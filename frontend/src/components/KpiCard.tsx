"use client";
import { Card, CardContent, Typography } from "@mui/material";

export default function KpiCard({
  label, value, hint, color = "primary.main",
}: {
  label: string;
  value: string | number;
  hint?: string;
  color?: string;
}) {
  return (
    <Card sx={{ minWidth: 180, flex: 1 }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography variant="h4" sx={{ color, fontWeight: 700, my: 0.5 }}>{value}</Typography>
        {hint && <Typography variant="caption" color="text.secondary">{hint}</Typography>}
      </CardContent>
    </Card>
  );
}
