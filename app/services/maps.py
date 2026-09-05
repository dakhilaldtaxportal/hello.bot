import re
import httpx

COORD_RE = re.compile(r"(?P<lat>-?\d{1,3}(?:\.\d+)?)\s*[,/ ]\s*(?P<lon>-?\d{1,3}(?:\.\d+)?)")

def parse_coordinates(value: str):
    m = COORD_RE.search(value or "")
    if not m:
        return None
    lat, lon = float(m.group("lat")), float(m.group("lon"))
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None

async def road_distance_km(lat1, lon1, lat2, lon2, base_url):
    url = f"{base_url}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    routes = data.get("routes") or []
    if not routes:
        raise RuntimeError("No driving route found")
    return routes[0]["distance"] / 1000.0
