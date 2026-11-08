import asyncpg

from hiking_app.models import CollectedPeak
from hiking_app.core.exceptions import POINotFound


CLAIM_SQL = """
INSERT INTO collected_pois (
    user_id,
    osm_type,
    osm_id
) VALUES ($1, $2, $3)
ON CONFLICT DO NOTHING
"""

UNCLAIM_SQL = """
DELETE FROM collected_pois
WHERE user_id = $1
  AND osm_type = $2
  AND osm_id = $3
"""

LIST_CLAIMS_SQL = """
SELECT
    p.osm_type,
    p.osm_id,
    p.name,
    p.ele,
    ST_Y(p.geom) AS lat,
    ST_X(p.geom) AS lon,
    c.collect_ts
FROM collected_pois c
JOIN pois p
  ON p.osm_type = c.osm_type
 AND p.osm_id   = c.osm_id
WHERE c.user_id = $1
ORDER BY c.collect_ts DESC
"""

class CollectionRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
    
    async def claim_poi(
        self,
        user_id: int, 
        osm_type: str, 
        osm_id: str,
        ) -> None:
        try:
            await self.conn.execute(CLAIM_SQL, user_id, osm_type, osm_id)
        except asyncpg.ForeignKeyViolationError as e:
            if e.constraint_name == "collected_pois_osm_type_osm_id_fkey":
                raise POINotFound() from e
            raise
    
    async def unclaim_poi(
        self,
        user_id: int, 
        osm_type: str, 
        osm_id: str,
        ) -> None:
        await self.conn.execute(UNCLAIM_SQL, user_id, osm_type, osm_id)
        
    async def list_claims(
        self,
        user_id: int,
    ) -> list[CollectedPeak]:
        rows = await self.conn.fetch(LIST_CLAIMS_SQL, user_id)
        return [_to_CollectedPeak_model(row) for row in rows]


def _to_CollectedPeak_model(record: asyncpg.Record) -> CollectedPeak:
    return CollectedPeak(
        osm_type=record["osm_type"],
        osm_id=record["osm_id"],
        name=record["name"],
        ele_m=record["ele"],
        lat=record["lat"],
        lon=record["lon"],
        collect_ts=record["collect_ts"],
    )