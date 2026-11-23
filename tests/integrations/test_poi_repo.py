from hiking_app.db import POIRepository

async def test_nearby_excludes_peaks_outside_radius(conn, origin, insert_poi):
    await insert_poi(1, distance_m=1000, name="Near")
    await insert_poi(2, distance_m=20000, name="Far")
    lat, lon = origin

    peaks = await POIRepository(conn).peaks_within_radius(lat, lon, radius_m=5000)

    assert len(peaks) == 1
    assert peaks[0].name == "Near"


async def test_nearby_excludes_other_kinds(conn, origin, insert_poi):
    await insert_poi(1, distance_m=1000, name="Peak")
    await insert_poi(2, distance_m=1000, kind="castle", name="hrad")
    lat, lon = origin

    peaks = await POIRepository(conn).peaks_within_radius(lat, lon, radius_m=5000)

    assert [p.name for p in peaks] == ["Peak"]


async def test_nearby_orders_by_distance(conn, origin, insert_poi):
    await insert_poi(1, distance_m=3000, name="Third")
    await insert_poi(2, distance_m=1000, name="First")
    await insert_poi(3, distance_m=2000, name="Second")
    lat, lon = origin

    peaks = await POIRepository(conn).peaks_within_radius(lat, lon, radius_m=5000)

    assert [p.name for p in peaks] == ["First", "Second", "Third"]


async def test_nearby_respects_limit(conn, origin, insert_poi):
    await insert_poi(1, distance_m=1000, name="First")
    await insert_poi(2, distance_m=2000, name="Second")
    await insert_poi(3, distance_m=3000, name="Third")
    lat, lon = origin

    peaks = await POIRepository(conn).peaks_within_radius(
        lat, lon, radius_m=5000, limit=2
    )

    assert [p.name for p in peaks] == ["First", "Second"]