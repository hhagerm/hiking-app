import json
from pathlib import Path
import asyncio

import asyncpg

from hiking_app.config import PG_DB_URL

DATA_FILE = Path("data/peaks.json")

SQL = """
INSERT INTO pois (osm_type, osm_id, kind, name, ele, tags, geom)
VALUES ($1, $2, $3, $4, $5, $6::jsonb, ST_SetSRID(ST_MakePoint($7, $8), 4326))
ON CONFLICT (osm_type, osm_id) DO NOTHING
"""

def parse_ele(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = ""
    for ch in raw.strip():
        if ch.isdigit() or ch in ".,-":
            cleaned += ch
        else:
            break
    
    cleaned = cleaned.rstrip(".,-").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        print(f"ValueError: {cleaned} couldnt be converted to float.")
        return None

def to_row(el: dict) -> tuple:
    tags = el.get("tags", {})
    lat = el.get("lat") or el["center"]["lat"]
    lon = el.get("lon") or el["center"]["lon"]

    return (
        el["type"][0],              # $1  'node' -> 'n'
        el["id"],                   # $2
        "peak",                     # $3  
        tags.get("name"),           # $4  None if unnamed
        parse_ele(tags.get("ele")), # $5  float or None
        json.dumps(tags),           # $6  dict -> JSON string for ::jsonb
        lon,                        # $7  ST_MakePoint takes X first
        lat,                        # $8
    )

async def main() -> None:
    raw = DATA_FILE.read_text(encoding="utf-8")
    data = json.loads(raw) 
    elements = data["elements"]
    rows = [to_row(el) for el in elements]

    conn = await asyncpg.connect(PG_DB_URL)
    try:
        await conn.executemany(SQL, rows)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())