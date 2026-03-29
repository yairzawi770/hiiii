import os
import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlarmService:
    def __init__(self, token: str, base_url: str, mongodb_client=None):
        self.token = token
        self.base_url = base_url
        self.mongodb_client = mongodb_client
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_alarm_history(
        self, 
        lat: float, 
        lon: float, 
        departure_time: int,
        lookback_days: int = 30
    ) -> Optional[dict]:
        """
        Query alarm history for a location.
        First tries to use MongoDB cache, then falls back to API.
        
        Args:
            lat, lon: Coordinates
            departure_time: Unix timestamp (seconds)
            lookback_days: How many days back to check (30 for last 30 days)
        
        Returns:
            { "alarm_count": int, "risk_score": float (0-1) }
        """
        try:
            # Try to get from MongoDB cache first
            if self.mongodb_client:
                cached = await self.mongodb_client.get_alarm_snapshot(
                    lat=lat,
                    lon=lon,
                    lookback_days=lookback_days
                )
                
                if cached:
                    # Check if cache is fresh (less than 1 hour old)
                    last_sync = cached.get("last_sync")
                    if isinstance(last_sync, datetime):
                        age_minutes = (datetime.utcnow() - last_sync).total_seconds() / 60
                        if age_minutes < 60:  # Cache valid for 1 hour
                            logger.info(f"Using cached alarm data for ({lat}, {lon}) - age: {age_minutes:.1f}min")
                            return {
                                "alarm_count": cached.get("alarm_count", 0),
                                "risk_score": cached.get("risk_score", 0.1),
                                "source": "cache"
                            }
            
            # Fall back to API call
            logger.info(f"Fetching fresh alarm data from API for ({lat}, {lon})")
            alarm_data = await self._fetch_from_api(lat, lon, departure_time, lookback_days)
            
            # Cache the result
            if self.mongodb_client and alarm_data:
                await self.mongodb_client.save_alarm_snapshot(
                    lat=lat,
                    lon=lon,
                    lookback_days=lookback_days,
                    alarm_count=alarm_data.get("alarm_count", 0),
                    risk_score=alarm_data.get("risk_score", 0.1),
                    alarms=alarm_data.get("alarms", [])
                )
            
            return alarm_data
        
        except Exception as e:
            logger.error(f"AlarmService error: {e}")
            return {
                "alarm_count": 0,
                "risk_score": 0.1,
                "error": str(e),
                "source": "error"
            }
    
    async def _fetch_from_api(self, lat: float, lon: float, 
                             departure_time: int, lookback_days: int) -> Optional[dict]:
        """Fetch alarm history from RedAlert API"""
        try:
            query_params = {
                "lat": lat,
                "lon": lon,
                "departure_time": departure_time,
                "lookback_days": lookback_days
            }
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Add explicit timeout for this specific request
            response = await asyncio.wait_for(
                self.client.get(
                    f"{self.base_url}",
                    params=query_params,
                    headers=headers
                ),
                timeout=3.0  # 3 second timeout for API call
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response and compute risk score
            alarm_count = data.get("count", 0)
            risk_score = min(1.0, alarm_count / 10.0)
            
            return {
                "alarm_count": alarm_count,
                "risk_score": risk_score,
                "raw_data": data,
                "source": "api"
            }
        except asyncio.TimeoutError:
            logger.warning(f"API timeout for ({lat}, {lon})")
            return None
        except Exception as e:
            logger.error(f"API fetch error: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()
