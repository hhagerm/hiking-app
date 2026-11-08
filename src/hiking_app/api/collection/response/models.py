from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CollectionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    osm_type: str
    osm_id: int
    name: str | None
    ele_m: float | None
    lat: float
    lon: float
    collect_ts: datetime