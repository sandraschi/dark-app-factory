"""Maps/location service — store/office locations, geocoding, nearby search."""

from __future__ import annotations

import logging
import math
import os
from typing import Any

logger = logging.getLogger("dark_factory")

_locations: list[dict] = []


def add_location(name: str, lat: float, lng: float, address: str = "", phone: str = "", hours: str = "", category: str = "") -> dict:
    loc = {"id": len(_locations) + 1, "name": name, "lat": lat, "lng": lng, "address": address, "phone": phone, "hours": hours, "category": category}
    _locations.append(loc)
    return loc


def list_locations(category: str | None = None) -> list[dict]:
    if category: return [l for l in _locations if l.get("category", "").lower() == category.lower()]
    return list(_locations)


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1); dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearby(lat: float, lng: float, radius_km: float = 10) -> list[dict]:
    results = []
    for loc in _locations:
        dist = _haversine(lat, lng, loc["lat"], loc["lng"])
        if dist <= radius_km:
            results.append({**loc, "distance_km": round(dist, 1)})
    return sorted(results, key=lambda x: x["distance_km"])
