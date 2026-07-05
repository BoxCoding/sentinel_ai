"""Google Maps Platform: routing, distance matrix, geocoding for emergency
dispatch. Demo mode returns synthetic routes over the demo city grid."""
import httpx

from app.core.config import settings

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class MapsService:
    async def best_route(self, origin: tuple[float, float],
                         destination: tuple[float, float],
                         avoid_flooded: bool = True) -> dict:
        if settings.DEMO_MODE or not settings.GOOGLE_MAPS_API_KEY:
            return self._demo_route(origin, destination, avoid_flooded)
        body = {
            "origin": {"location": {"latLng": {"latitude": origin[0], "longitude": origin[1]}}},
            "destination": {"location": {"latLng": {"latitude": destination[0], "longitude": destination[1]}}},
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        }
        headers = {
            "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(ROUTES_URL, json=body, headers=headers, timeout=15)
            resp.raise_for_status()
            route = resp.json()["routes"][0]
        return {
            "duration_s": int(route["duration"].rstrip("s")),
            "distance_m": route["distanceMeters"],
            "polyline": route["polyline"]["encodedPolyline"],
            "avoided_hazards": [],
        }

    async def geocode(self, address: str) -> tuple[float, float]:
        if settings.DEMO_MODE or not settings.GOOGLE_MAPS_API_KEY:
            # demo: Delhi NCR center with a deterministic offset per address
            offset = (sum(ord(c) for c in address) % 100) / 1000
            return (28.6139 + offset, 77.2090 + offset)
        async with httpx.AsyncClient() as client:
            resp = await client.get(GEOCODE_URL, params={
                "address": address, "key": settings.GOOGLE_MAPS_API_KEY,
            }, timeout=15)
            loc = resp.json()["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])

    def _demo_route(self, origin, destination, avoid_flooded) -> dict:
        dist_km = (abs(origin[0] - destination[0]) + abs(origin[1] - destination[1])) * 111
        avoided = (["Minto Bridge Underpass (waterlogged)", "Andheri Subway (flooded)"]
                   if avoid_flooded else [])
        detour = 1.25 if avoided else 1.0
        return {
            "duration_s": int(dist_km * detour / 40 * 3600),  # 40 km/h urban emergency speed
            "distance_m": int(dist_km * detour * 1000),
            "polyline": "",
            "avoided_hazards": avoided,
        }


maps = MapsService()
