import logging
import httpx
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


class AlarmSyncTask:
    """Background task to sync alarms from RedAlert API to MongoDB"""
    
    def __init__(self, token: str, api_url: str, mongodb_client, sync_interval_minutes: int = 5):
        self.token = token
        self.api_url = api_url
        self.mongodb_client = mongodb_client
        self.sync_interval_minutes = sync_interval_minutes
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.last_sync = None
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Alarm sync task already running")
            return
        
        self.scheduler = AsyncIOScheduler()
        
        # Add the sync job
        self.scheduler.add_job(
            self._sync_alarms,
            'interval',
            minutes=self.sync_interval_minutes,
            id='alarm_sync_job'
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"✅ Alarm sync task started (interval: {self.sync_interval_minutes} minutes)")
        
        # Run initial sync immediately
        await self._sync_alarms()
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Alarm sync task stopped")
    
    async def _sync_alarms(self):
        """Fetch new alarms from API and store in MongoDB"""
        try:
            logger.info("🔄 Starting alarm sync from RedAlert API...")
            
            # Get alarms from last hour
            alarms = await self._fetch_recent_alarms_from_api()
            
            if alarms and len(alarms) > 0:
                logger.info(f"📥 Fetched {len(alarms)} new alarms from API")
                
                # Store in MongoDB
                stored_count = await self.mongodb_client.add_alarms_batch(alarms)
                logger.info(f"💾 Stored {stored_count} alarms in MongoDB")
                
                self.last_sync = datetime.utcnow()
            else:
                logger.info("No new alarms fetched")
                self.last_sync = datetime.utcnow()
        
        except Exception as e:
            logger.error(f"❌ Alarm sync error: {e}")
    
    async def _fetch_recent_alarms_from_api(self) -> list:
        """
        Fetch recent alarms from RedAlert API.
        This is a simplified implementation - adjust based on actual API response.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Query last hour of alarms
                now = datetime.utcnow()
                one_hour_ago = now - timedelta(hours=1)
                
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {
                    "from": int(one_hour_ago.timestamp()),
                    "to": int(now.timestamp()),
                    "limit": 1000
                }
                
                response = await client.get(
                    self.api_url,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Parse and normalize alarms
                # This structure depends on RedAlert API actual response
                alarms = self._parse_api_response(data)
                return alarms
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching alarms: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching alarms: {e}")
            return []
    
    def _parse_api_response(self, data: dict) -> list:
        """Parse RedAlert API response into alarm records"""
        alarms = []
        
        try:
            # Handle different possible response formats
            # Adjust this based on actual API response structure
            
            if isinstance(data, dict):
                # If response has a 'data' or 'results' key
                alarm_list = data.get('data') or data.get('results') or data.get('alarms') or []
            elif isinstance(data, list):
                alarm_list = data
            else:
                logger.warning(f"Unexpected API response format: {type(data)}")
                return []
            
            for alarm_data in alarm_list:
                try:
                    alarm = {
                        "lat": float(alarm_data.get("latitude") or alarm_data.get("lat") or 0),
                        "lon": float(alarm_data.get("longitude") or alarm_data.get("lon") or 0),
                        "timestamp": int(alarm_data.get("timestamp") or alarm_data.get("time") or 0),
                        "severity": alarm_data.get("severity") or alarm_data.get("level"),
                        "category": alarm_data.get("category") or alarm_data.get("type"),
                        "description": alarm_data.get("description") or alarm_data.get("title"),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    # Only add if we have valid coordinates and timestamp
                    if alarm["lat"] and alarm["lon"] and alarm["timestamp"]:
                        alarms.append(alarm)
                
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing alarm record: {e}")
                    continue
            
            logger.info(f"Parsed {len(alarms)} alarm records from API response")
            return alarms
        
        except Exception as e:
            logger.error(f"Error parsing API response: {e}")
            return []
    
    def get_status(self) -> dict:
        """Get sync task status"""
        return {
            "is_running": self.is_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_interval_minutes": self.sync_interval_minutes
        }


# Global instance
alarm_sync_task: Optional[AlarmSyncTask] = None


async def get_alarm_sync_task() -> AlarmSyncTask:
    """Get or create alarm sync task"""
    global alarm_sync_task
    if alarm_sync_task is None:
        raise RuntimeError("Alarm sync task not initialized")
    return alarm_sync_task
