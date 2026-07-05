"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Alert, Box, Button, Card, CardContent, Stack, TextField, Typography,
} from "@mui/material";
import ShieldIcon from "@mui/icons-material/Shield";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("commander");
  const [password, setPassword] = useState("command123");
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      router.push("/");
    } catch {
      setError("Invalid credentials");
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <Card sx={{ width: 400 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" sx={{ mb: 3 }}>
            <ShieldIcon sx={{ fontSize: 48, color: "primary.main" }} />
            <Typography variant="h5" sx={{ mt: 1 }}>Sentinel AI</Typography>
            <Typography variant="body2" color="text.secondary">
              Emergency Decision Intelligence Platform
            </Typography>
          </Stack>
          <form onSubmit={submit}>
            <Stack spacing={2}>
              {error && <Alert severity="error">{error}</Alert>}
              <TextField label="Username" value={username} fullWidth
                         onChange={(e) => setUsername(e.target.value)} />
              <TextField label="Password" type="password" value={password} fullWidth
                         onChange={(e) => setPassword(e.target.value)} />
              <Button type="submit" variant="contained" size="large">Sign in</Button>
              <Typography variant="caption" color="text.secondary" align="center">
                Demo: commander/command123 · admin/admin123 · citizen/citizen123
              </Typography>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
