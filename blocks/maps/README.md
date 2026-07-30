# Maps Block

Location and maps — Leaflet/MapLibre integration, store locator, geocoding, service area map, and directions link.

**Triggers**: map, location, directions, address, store.locator, find.us, driving, branches

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `MAPS_CENTER_LAT` | `48.2082` | Default map center latitude |
| `MAPS_CENTER_LNG` | `16.3738` | Default map center longitude |
| `MAPS_ZOOM` | `13` | Default zoom level |

**API endpoints**: `/api/maps/locations`, `/api/maps/nearby`

**Dependencies**: `npm: leaflet, leaflet.markercluster`
