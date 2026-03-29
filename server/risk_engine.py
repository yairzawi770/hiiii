import math
import logging
import asyncio
from typing import List, Tuple

from schemas import Point, Segment, CheckpointRisk

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Computes trip risk by:
    1. Extracting 3 interior checkpoints (25%, 50%, 75% along route)
    2. Querying alarm history for each checkpoint + origin/destination
    3. Computing base route segment risks
    4. Weighting and normalizing into overall tripRisk
    """
    
    def __init__(self, alarm_service):
        self.alarm_service = alarm_service
        self.ORIGIN_WEIGHT = 0.15
        self.DEST_WEIGHT = 0.15
        self.MID_WEIGHT = 0.20  # Each midpoint: 0.20/3 ≈ 0.067
        self.ROUTE_WEIGHT = 0.50
    
    def _interpolate_point(self, coords: List[Point], t: float) -> Point:
        """Interpolate point at position t (0.0–1.0) along route."""
        if not coords or t < 0 or t > 1:
            return coords[0] if coords else Point(lat=0, lon=0)
        
        if t == 0:
            return coords[0]
        if t == 1:
            return coords[-1]
        
        # Linear progression through indices
        idx_float = t * (len(coords) - 1)
        idx_low = int(idx_float)
        idx_high = min(idx_low + 1, len(coords) - 1)
        frac = idx_float - idx_low
        
        p_low = coords[idx_low]
        p_high = coords[idx_high]
        
        lat = p_low.lat + (p_high.lat - p_low.lat) * frac
        lon = p_low.lon + (p_high.lon - p_low.lon) * frac
        return Point(lat=lat, lon=lon)
    
    async def calculate_trip_risk(
        self, 
        coordinates: List[Point], 
        departure_time: int
    ) -> Tuple[float, List[Segment], List[CheckpointRisk]]:
        """Wrapper with timeout protection."""
        print(f"🟢 RiskEngine: calculate_trip_risk called with {len(coordinates)} coords")
        try:
            result = await asyncio.wait_for(
                self._calculate_trip_risk_impl(coordinates, departure_time),
                timeout=12.0
            )
            print(f"🟢 RiskEngine: Complete - trip_risk={result[0]:.2%}")
            return result
        except asyncio.TimeoutError:
            print(f"🔴 RiskEngine: TIMEOUT after 12 seconds")
            # Safe fallback
            return (0.5, [], [])
        except Exception as e:
            print(f"🔴 RiskEngine: ERROR - {e}")
            import traceback
            traceback.print_exc()
            return (0.5, [], [])
    
    async def _calculate_trip_risk_impl(
        self, 
        coordinates: List[Point], 
        departure_time: int
    ) -> Tuple[float, List[Segment], List[CheckpointRisk]]:
        """
        Main method: compute overall tripRisk and breakdowns.
        
        Returns:
            (trip_risk: 0.0–1.0, segments: List[Segment], checkpoints: List[CheckpointRisk])
        """
        if len(coordinates) < 2:
            raise ValueError("Need at least 2 coordinate points")
        
        # 1. Get 5 checkpoints: origin, destination, and 3 midpoints
        checkpoints_data = [
            (coordinates[0], "origin", 0.0),
            (coordinates[-1], "destination", 1.0),
            (self._interpolate_point(coordinates, 0.25), "midpoint_25", 0.25),
            (self._interpolate_point(coordinates, 0.50), "midpoint_50", 0.50),
            (self._interpolate_point(coordinates, 0.75), "midpoint_75", 0.75),
        ]
        
        # 2. Query alarm history for EACH checkpoint in parallel
        print(f"🟡 RiskEngine: Querying {len(checkpoints_data)} checkpoints in parallel...")
        checkpoint_tasks = [
            self.alarm_service.get_alarm_history(
                lat=point.lat,
                lon=point.lon,
                departure_time=departure_time,
                lookback_days=30
            )
            for point, cp_type, _ in checkpoints_data
        ]
        alarm_datas = await asyncio.gather(*checkpoint_tasks, return_exceptions=True)
        
        checkpoint_risks = []
        checkpoint_risk_values = []
        for (point, cp_type, _), alarm_data in zip(checkpoints_data, alarm_datas):
            # Handle exceptions from parallel queries
            if isinstance(alarm_data, Exception):
                print(f"🟡 RiskEngine: Query failed for {cp_type}: {alarm_data}")
                alarm_risk = 0.1
            else:
                alarm_risk = alarm_data.get("risk_score", 0.1) if alarm_data else 0.1
            
            checkpoint_risks.append(CheckpointRisk(
                location=point,
                checkpoint_type=cp_type,
                alarm_risk=alarm_risk,
                base_risk=None
            ))
            checkpoint_risk_values.append(alarm_risk)
        
        # 3. Compute route segment risks (simple gradient + noise based on checkpoint risks)
        segments = []
        for i in range(len(coordinates) - 1):
            p1, p2 = coordinates[i], coordinates[i + 1]
            t = i / max(1, len(coordinates) - 2)  # Progress 0..1
            
            # Interpolate risk based on nearby checkpoints
            base_risk = 0.3 + 0.4 * t + 0.1 * math.sin(t * math.pi * 4)
            base_risk = max(0.0, min(1.0, base_risk))
            
            segments.append(Segment(
                coords=[p1, p2],
                risk=base_risk
            ))
        
        # 4. Compute weights and overall tripRisk
        route_avg_risk = sum(s.risk for s in segments) / len(segments) if segments else 0.5
        checkpoint_avg_risk = sum(checkpoint_risk_values) / len(checkpoint_risk_values) if checkpoint_risk_values else 0.5
        
        trip_risk = (
            self.ORIGIN_WEIGHT * checkpoint_risk_values[0] +  # origin
            self.DEST_WEIGHT * checkpoint_risk_values[1] +    # destination
            (self.MID_WEIGHT / 3) * sum(checkpoint_risk_values[2:5]) +  # 3 midpoints
            self.ROUTE_WEIGHT * route_avg_risk
        )
        trip_risk = max(0.0, min(1.0, trip_risk))  # Clamp to [0, 1]
        
        return trip_risk, segments, checkpoint_risks
