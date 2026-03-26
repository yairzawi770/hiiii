from pydantic import BaseModel
from typing import List, Optional


class Point(BaseModel):
    lat: float
    lon: float


class Segment(BaseModel):
    coords: List[Point]      # [from_point, to_point]
    risk: float              # 0.0–1.0


class CheckpointRisk(BaseModel):
    location: Point
    checkpoint_type: str     # "origin", "destination", "midpoint_25", "midpoint_50", "midpoint_75"
    alarm_risk: float        # Risk from alarm history (0.0–1.0)
    base_risk: Optional[float] = None  # Baseline geographic risk (optional)


class TripRequest(BaseModel):
    coordinates: List[Point] # Full route coordinates from DirectionsService
    departure_time: int      # Unix timestamp (seconds)


class TripRiskResponse(BaseModel):
    trip_risk: float         # Overall risk (0.0–1.0)
    segments: List[Segment]  # Per-segment breakdown
    checkpoints: List[CheckpointRisk]  # 5 checkpoints: origin, dest, mid1/2/3
    metadata: dict           # { "total_distance_m": ..., "route_points": ..., etc. }
