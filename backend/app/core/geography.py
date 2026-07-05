"""Authoritative geography for the demo metros. The data generator and the
live-weather feed both read from here so district metadata never drifts.

relative_elev_m is elevation above the local river/drainage level (0-120
scale) — it feeds the flood model directly, NOT absolute altitude.
"""

# district -> dict(city, lat, lng, relative_elev_m, flood_prone, drainage_capacity)
DISTRICT_META: dict[str, dict] = {
    # Delhi NCR
    "Connaught Place": {"city": "Delhi NCR", "lat": 28.6315, "lng": 77.2167,
                        "relative_elev_m": 60, "flood_prone": False, "drainage": 48},
    "Gurugram":        {"city": "Delhi NCR", "lat": 28.4595, "lng": 77.0266,
                        "relative_elev_m": 35, "flood_prone": True, "drainage": 34},
    "Noida":           {"city": "Delhi NCR", "lat": 28.5355, "lng": 77.3910,
                        "relative_elev_m": 45, "flood_prone": False, "drainage": 46},
    "Dwarka":          {"city": "Delhi NCR", "lat": 28.5921, "lng": 77.0460,
                        "relative_elev_m": 55, "flood_prone": False, "drainage": 47},
    "Yamuna Bank":     {"city": "Delhi NCR", "lat": 28.6230, "lng": 77.2730,
                        "relative_elev_m": 8, "flood_prone": True, "drainage": 30},
    # Mumbai
    "Colaba":          {"city": "Mumbai", "lat": 18.9067, "lng": 72.8147,
                        "relative_elev_m": 25, "flood_prone": False, "drainage": 45},
    "Bandra":          {"city": "Mumbai", "lat": 19.0596, "lng": 72.8295,
                        "relative_elev_m": 20, "flood_prone": False, "drainage": 44},
    "Andheri":         {"city": "Mumbai", "lat": 19.1197, "lng": 72.8468,
                        "relative_elev_m": 12, "flood_prone": True, "drainage": 33},
    "Kurla":           {"city": "Mumbai", "lat": 19.0650, "lng": 72.8790,
                        "relative_elev_m": 6, "flood_prone": True, "drainage": 30},
    "Dadar":           {"city": "Mumbai", "lat": 19.0178, "lng": 72.8478,
                        "relative_elev_m": 30, "flood_prone": False, "drainage": 46},
    # Bengaluru
    "Koramangala":     {"city": "Bengaluru", "lat": 12.9352, "lng": 77.6245,
                        "relative_elev_m": 18, "flood_prone": True, "drainage": 35},
    "Whitefield":      {"city": "Bengaluru", "lat": 12.9698, "lng": 77.7500,
                        "relative_elev_m": 50, "flood_prone": False, "drainage": 47},
    "Indiranagar":     {"city": "Bengaluru", "lat": 12.9719, "lng": 77.6412,
                        "relative_elev_m": 45, "flood_prone": False, "drainage": 46},
    "Bellandur":       {"city": "Bengaluru", "lat": 12.9257, "lng": 77.6770,
                        "relative_elev_m": 10, "flood_prone": True, "drainage": 31},
    "Hebbal":          {"city": "Bengaluru", "lat": 13.0358, "lng": 77.5970,
                        "relative_elev_m": 65, "flood_prone": False, "drainage": 48},
}

# hospital -> dict(city, district, lat, lng, beds)
HOSPITAL_META: dict[str, dict] = {
    "AIIMS Delhi":          {"city": "Delhi NCR", "district": "Connaught Place",
                             "lat": 28.5672, "lng": 77.2100, "beds": 800},
    "Medanta Gurugram":     {"city": "Delhi NCR", "district": "Gurugram",
                             "lat": 28.4390, "lng": 77.0410, "beds": 550},
    "Fortis Noida":         {"city": "Delhi NCR", "district": "Noida",
                             "lat": 28.5670, "lng": 77.3250, "beds": 300},
    "Lilavati Mumbai":      {"city": "Mumbai", "district": "Bandra",
                             "lat": 19.0510, "lng": 72.8280, "beds": 320},
    "KEM Mumbai":           {"city": "Mumbai", "district": "Dadar",
                             "lat": 19.0030, "lng": 72.8410, "beds": 450},
    "Manipal Bengaluru":    {"city": "Bengaluru", "district": "Indiranagar",
                             "lat": 12.9590, "lng": 77.6480, "beds": 600},
    "St. John's Bengaluru": {"city": "Bengaluru", "district": "Koramangala",
                             "lat": 12.9300, "lng": 77.6190, "beds": 350},
}
