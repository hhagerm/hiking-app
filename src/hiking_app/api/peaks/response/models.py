from pydantic import BaseModel, ConfigDict


class PeaksNearbyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    osm_type: str
    osm_id: int
    name: str | None
    ele_m: float | None
    lat: float
    lon: float
    distance_m: float