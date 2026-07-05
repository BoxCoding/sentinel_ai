"use client";

const BASE = "/api/v1";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

export function getRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_role");
}

export async function login(username: string, password: string) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  localStorage.setItem("sentinel_token", data.access_token);
  localStorage.setItem("sentinel_role", data.role);
  return data;
}

export function logout() {
  localStorage.removeItem("sentinel_token");
  localStorage.removeItem("sentinel_role");
  window.location.href = "/login";
}

async function request(path: string, init: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (res.status === 401 && typeof window !== "undefined") {
    logout();
    // We're navigating to /login; never settle so no caller sees a
    // transient rejection mid-redirect (avoids unhandled-rejection noise).
    return new Promise(() => {});
  }
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  get: (path: string) => request(path),
  post: (path: string, body?: unknown) =>
    request(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
    }),
  patch: (path: string) => request(path, { method: "PATCH" }),
};
