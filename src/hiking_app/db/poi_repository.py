import asyncpg

from hiking_app.models import PeakDistance

NEARBY_PEAKS_SQL = """
SELECT
    osm_type,
    osm_id,
    name,
    ele,
    ST_Y(geom) AS lat,
    ST_X(geom) AS lon,
    ST_Distance(
        geom::geography,
        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
    ) AS distance_m
FROM pois
WHERE kind = 'peak'
  AND ST_DWithin(
        geom::geography,
        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
        $3
      )
ORDER BY distance_m
LIMIT $4
"""

class POIRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
    
    
    
    async def peaks_within_radius(
        self,
        lat: float, 
        lon: float, 
        radius_m: int = 5000, 
        limit: int = 50
        ) -> list[PeakDistance]:
        rows = await self.conn.fetch(NEARBY_PEAKS_SQL, lon, lat, radius_m, limit)
        return [_to_PeakDistance_model(row) for row in rows]
    
def _to_PeakDistance_model( 
    record: asyncpg.Record
    ) -> PeakDistance:
    return PeakDistance(
        osm_type=record["osm_type"],
        osm_id=record["osm_id"],
        name=record["name"],
        ele_m=record["ele"],
        lat=record["lat"],
        lon=record["lon"],
        distance_m=record["distance_m"]
        )