"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AppBar, Box, Chip, Drawer, IconButton, List, ListItemButton,
  ListItemIcon, ListItemText, Toolbar, Typography,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import MapIcon from "@mui/icons-material/Map";
import InsightsIcon from "@mui/icons-material/Insights";
import ChatIcon from "@mui/icons-material/Chat";
import LocalHospitalIcon from "@mui/icons-material/LocalHospital";
import TrafficIcon from "@mui/icons-material/Traffic";
import CloudIcon from "@mui/icons-material/Cloud";
import TimelineIcon from "@mui/icons-material/Timeline";
import AssessmentIcon from "@mui/icons-material/Assessment";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import LogoutIcon from "@mui/icons-material/Logout";
import MyLocationIcon from "@mui/icons-material/MyLocation";
import ShieldIcon from "@mui/icons-material/Shield";
import { getRole, getToken, logout } from "@/lib/api";

const NAV = [
  { href: "/", label: "Home", icon: <DashboardIcon /> },
  { href: "/map", label: "Emergency Map", icon: <MapIcon /> },
  { href: "/location", label: "My Location", icon: <MyLocationIcon /> },
  { href: "/predictions", label: "Predictions", icon: <InsightsIcon /> },
  { href: "/chat", label: "AI Chat", icon: <ChatIcon /> },
  { href: "/hospitals", label: "Hospitals", icon: <LocalHospitalIcon /> },
  { href: "/traffic", label: "Traffic", icon: <TrafficIcon /> },
  { href: "/weather", label: "Weather", icon: <CloudIcon /> },
  { href: "/timeline", label: "Incident Timeline", icon: <TimelineIcon /> },
  { href: "/reports", label: "Reports", icon: <AssessmentIcon /> },
  { href: "/admin", label: "Admin", icon: <AdminPanelSettingsIcon />, role: "admin" },
];

const WIDTH = 240;

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setRole(getRole());
  }, [router]);

  if (role === null) return null;

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar position="fixed" elevation={0}
              sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: "#FFFFFF",
                    color: "text.primary", borderBottom: "1px solid #E2E8F0" }}>
        <Toolbar>
          <ShieldIcon sx={{ mr: 1.5, color: "primary.main" }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Sentinel AI
            <Typography component="span" variant="body2" sx={{ ml: 1.5, color: "text.secondary" }}>
              Emergency Decision Intelligence
            </Typography>
          </Typography>
          <Chip size="small" label={role.toUpperCase()} color="primary" variant="outlined" sx={{ mr: 2 }} />
          <IconButton onClick={logout} aria-label="Log out" color="inherit">
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: WIDTH,
          [`& .MuiDrawer-paper`]: { width: WIDTH, bgcolor: "#FFFFFF", borderRight: "1px solid #E2E8F0" },
        }}
      >
        <Toolbar />
        <List>
          {NAV.filter((n) => !n.role || n.role === role).map((n) => (
            <ListItemButton
              key={n.href}
              component={Link}
              href={n.href}
              selected={pathname === n.href}
              sx={{ borderRadius: 2, mx: 1, my: 0.25 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{n.icon}</ListItemIcon>
              <ListItemText primary={n.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
