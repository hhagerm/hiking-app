from dataclasses import dataclass

@dataclass(frozen=True)
class Peak:
    osm_type: str
    osm_id: int
    name: str | None
    ele_m: float | None
    lat: float
    lon: float
    
@dataclass(frozen=True)
class PeakDistance(Peak):
    distance_m: float