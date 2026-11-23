import os 

import asyncpg
import pytest

from hiking_app.core.config import build_db_url

TEST_DB_URL = build_db_url(
    user=os.getenv("TEST_POSTGRES_USER"),
    password=os.getenv("TEST_POSTGRES_PASSWORD"),
    host="localhost",
    port=int(os.getenv("TEST_POSTGRES_PORT")),
    name=os.getenv("TEST_POSTGRES_DB"),
)

@pytest.fixture(scope="session")
async def pool():
    pool = await asyncpg.create_pool(TEST_DB_URL)
    yield pool
    await pool.close()
    
@pytest.fixture(autouse=True)
async def clean_db(pool):
    await pool.execute(
        "TRUNCATE TABLE collected_pois, sessions, users, pois RESTART IDENTITY CASCADE"
    )
    yield
    
@pytest.fixture
async def conn(pool):
    async with pool.acquire() as conn:
        yield conn
        
ORIGIN_LAT = 50.73
ORIGIN_LON = 15.74

INSERT_POI_AT = """
INSERT INTO pois (osm_type, osm_id, kind, name, ele, geom)
VALUES ($1, $2, $3, $4, $5,
        ST_Project(
            ST_SetSRID(ST_MakePoint($6, $7), 4326)::geography,
            $8::double precision, radians($9)
        )::geometry)
"""


@pytest.fixture
def origin():
    return ORIGIN_LAT, ORIGIN_LON


@pytest.fixture
def insert_poi(conn):
    async def _insert(osm_id, *, distance_m, bearing_deg=0,
                      kind="peak", name="Test Peak", ele=1000):
        await conn.execute(
            INSERT_POI_AT, "n", osm_id, kind, name, ele,
            ORIGIN_LON, ORIGIN_LAT, distance_m, bearing_deg,
        )
        return "n", osm_id

    return _insert