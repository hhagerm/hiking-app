# FastAPI & PostGIS Peak Collection App

> **Status:** early stages — the core loop works, the feature set is still small and unrefined.

A web app for collecting mountain peaks. Peaks are imported from OpenStreetMap into
a PostGIS database, browsed on a topographic map, and claimed one by one into a
personal collection. An asynchronous FastAPI application serves both the JSON API
and the frontend; PostGIS answers the spatial queries; sessions are cookie-based
with hashed opaque tokens.

The frontend is plain ES modules with no build step and no framework — the server
mounts `static/` directly, so there is nothing to compile before running it. Full
disclosure: it is vibe-coded. The backend is not.

## Architecture

* **API:** FastAPI on uvicorn, split into routers per resource (`/peaks`, `/user`,
  `/collection`). Request and response bodies are Pydantic models, so the schema is
  the contract and the interactive docs come for free at `/docs`.
* **Layering:** routers depend on a service or a repository, never on each other.
  `UserService` owns registration and login rules; the repositories own SQL and
  return domain models. Wiring happens in one place, `core/dependencies.py`, through
  FastAPI's dependency injection — including the per-request connection acquired
  from the asyncpg pool.
* **Geospatial:** peaks are stored as `GEOMETRY(Point, 4326)` behind a GIST index.
  "Peaks near me" is a single `ST_DWithin` on the geography type with `ST_Distance`
  for the ordering, so the radius search and the distances are computed in the
  database rather than in Python.
* **Authentication:** passwords hashed with Argon2. Login issues a 256-bit opaque
  token, stores only its SHA-256 hash, and returns it in an `httponly` cookie with a
  30-day TTL. An unknown username is still verified against a dummy hash, so a
  failed login costs the same time whether or not the account exists.
* **Database:** PostgreSQL with the PostGIS extension, schema managed by yoyo
  migrations and applied by a one-shot container that waits on the database
  healthcheck.
* **Frontend:** vanilla ES modules behind a hash router, with Leaflet and
  OpenTopoMap tiles for the map. Shared state (the session, the claimed set) lives
  in its own modules with a subscription API, so the map pins, the list rows and the
  marker popups all repaint from one source of truth. Claims are optimistic and roll
  back if the request fails.
* **Data:** peaks come from an Overpass API export, normalized and loaded by
  `scripts/load_pois.py`. OSM type and id are the primary key and the load is
  idempotent, so re-running it against a newer export only adds what is missing.
