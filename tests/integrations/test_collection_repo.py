from datetime import datetime, timedelta, timezone

import pytest

from hiking_app.core.exceptions import POINotFound
from hiking_app.db import CollectionRepository

MISSING_PEAK = ("n", 999_999)


def minutes_ago(minutes: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


@pytest.fixture
def insert_user(conn):
    async def _insert(username):
        row = await conn.fetchrow(
            "INSERT INTO users (email, username, password_hash) "
            "VALUES ($1, $2, $3) RETURNING id",
            f"{username}@example.com",
            username,
            "fake-argon2-hash",
        )
        return row["id"]

    return _insert


@pytest.fixture
async def user_id(insert_user):
    return await insert_user("collector")


@pytest.fixture
async def other_user_id(insert_user):
    return await insert_user("other_collector")


@pytest.fixture
async def peak(insert_poi):
    return await insert_poi(1, distance_m=0, name="Snezka")


@pytest.fixture
async def second_peak(insert_poi):
    return await insert_poi(2, distance_m=1000, name="Lysa hora")


@pytest.fixture
def claim_at(conn):
    async def _claim(user_id, peak, *, collect_ts):
        osm_type, osm_id = peak
        await conn.execute(
            "INSERT INTO collected_pois (user_id, osm_type, osm_id, collect_ts) "
            "VALUES ($1, $2, $3, $4)",
            user_id,
            osm_type,
            osm_id,
            collect_ts,
        )

    return _claim


async def test_claim_poi_stores_claim_listed_for_user(conn, user_id, peak):
    repo = CollectionRepository(conn)
    await repo.claim_poi(user_id, *peak)

    claims = await repo.list_claims(user_id)

    assert len(claims) == 1
    assert (claims[0].osm_type, claims[0].osm_id) == peak
    assert claims[0].name == "Snezka"
    assert claims[0].ele_m == 1000
    assert claims[0].lat == pytest.approx(50.73)
    assert claims[0].lon == pytest.approx(15.74)
    assert claims[0].collect_ts is not None


async def test_claim_poi_claiming_twice_keeps_one_claim(conn, user_id, peak):
    repo = CollectionRepository(conn)
    await repo.claim_poi(user_id, *peak)
    await repo.claim_poi(user_id, *peak)

    claims = await repo.list_claims(user_id)

    assert len(claims) == 1


async def test_claim_poi_raises_poi_not_found_when_peak_missing(conn, user_id):
    with pytest.raises(POINotFound):
        await CollectionRepository(conn).claim_poi(user_id, *MISSING_PEAK)


async def test_unclaim_poi_removes_claim(conn, user_id, peak):
    repo = CollectionRepository(conn)
    await repo.claim_poi(user_id, *peak)

    await repo.unclaim_poi(user_id, *peak)

    assert await repo.list_claims(user_id) == []


async def test_unclaim_poi_leaves_claims_of_other_users(
    conn, user_id, other_user_id, peak
):
    repo = CollectionRepository(conn)
    await repo.claim_poi(user_id, *peak)
    await repo.claim_poi(other_user_id, *peak)

    await repo.unclaim_poi(user_id, *peak)

    assert await repo.list_claims(user_id) == []
    assert len(await repo.list_claims(other_user_id)) == 1


async def test_list_claims_returns_only_claims_of_given_user(
    conn, user_id, other_user_id, peak, second_peak
):
    repo = CollectionRepository(conn)
    await repo.claim_poi(user_id, *peak)
    await repo.claim_poi(other_user_id, *second_peak)

    claims = await repo.list_claims(user_id)

    assert [claim.name for claim in claims] == ["Snezka"]


async def test_list_claims_returns_empty_list_when_user_has_no_claims(conn, user_id):
    claims = await CollectionRepository(conn).list_claims(user_id)

    assert claims == []


async def test_list_claims_orders_newest_first(
    conn, user_id, peak, second_peak, claim_at
):
    await claim_at(user_id, peak, collect_ts=minutes_ago(10))
    await claim_at(user_id, second_peak, collect_ts=minutes_ago(1))

    claims = await CollectionRepository(conn).list_claims(user_id)

    assert [claim.name for claim in claims] == ["Lysa hora", "Snezka"]
