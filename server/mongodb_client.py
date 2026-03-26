import os
import logging
import math
from datetime import datetime, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import numpy as np
from pymongo import ASCENDING, DESCENDING, GEO2D
import json

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Async MongoDB client for alarm data storage"""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Initialize MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(self.connection_url)
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client.safe_travel
            await self._create_indexes()
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")
    
    async def _create_indexes(self):
        """Create necessary indexes for efficient queries"""
        alarms_col = self.db.alarms
        snapshots_col = self.db.alarm_snapshots
        
        # Index for alarms: (lat, lon, timestamp)
        await alarms_col.create_index([
            ("lat", ASCENDING),
            ("lon", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        # Index for time-based queries
        await alarms_col.create_index([("timestamp", DESCENDING)])
        
        # Index for snapshots: (lat, lon, lookback_days)
        await snapshots_col.create_index([
            ("lat", ASCENDING),
            ("lon", ASCENDING),
            ("lookback_days", ASCENDING)
        ], unique=True)
        
        # TTL index: auto-delete old snapshots after 24 hours
        await snapshots_col.create_index(
            [("last_sync", ASCENDING)],
            expireAfterSeconds=86400  # 24 hours
        )
        
        logger.info("✅ Indexes created")
    
    async def add_alarm(self, lat: float, lon: float, timestamp: int, 
                       severity: Optional[str] = None, 
                       category: Optional[str] = None,
                       description: Optional[str] = None) -> dict:
        """Add a single alarm to the database"""
        alarm = {
            "lat": lat,
            "lon": lon,
            "timestamp": timestamp,
            "severity": severity,
            "category": category,
            "description": description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.db.alarms.insert_one(alarm)
        alarm["_id"] = result.inserted_id
        logger.info(f"Added alarm at ({lat}, {lon}) - timestamp {timestamp}")
        return alarm
    
    async def add_alarms_batch(self, alarms: List[dict]) -> int:
        """Add multiple alarms at once"""
        if not alarms:
            return 0
        
        result = await self.db.alarms.insert_many(alarms)
        logger.info(f"Added {len(result.inserted_ids)} alarms")
        return len(result.inserted_ids)
    
    async def get_alarms_in_range(self, lat: float, lon: float, 
                                  lookback_days: int = 30,
                                  radius_km: float = 50) -> List[dict]:
        """
        Get alarms within a geographic radius and time range.
        
        Args:
            lat, lon: Center point
            lookback_days: How many days back to query
            radius_km: Search radius in kilometers
        """
        cutoff_timestamp = int((datetime.utcnow() - timedelta(days=lookback_days)).timestamp())
        
        # Simple lat/lon bounding box (not perfect, but good enough for MVP)
        # Rough conversion: 1 degree ≈ 111 km
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(np.cos(np.radians(lat)))) if lat != 0 else radius_km / 111.0
        
        alarms = await self.db.alarms.find({
            "lat": {"$gte": lat - lat_delta, "$lte": lat + lat_delta},
            "lon": {"$gte": lon - lon_delta, "$lte": lon + lon_delta},
            "timestamp": {"$gte": cutoff_timestamp}
        }).sort("timestamp", DESCENDING).to_list(1000)
        
        return alarms
    
    async def get_recent_alarms(self, hours: int = 1) -> List[dict]:
        """Get alarms from the last N hours"""
        cutoff_timestamp = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())
        alarms = await self.db.alarms.find({
            "timestamp": {"$gte": cutoff_timestamp}
        }).sort("timestamp", DESCENDING).to_list(100)
        return alarms
    
    async def save_alarm_snapshot(self, lat: float, lon: float, 
                                  lookback_days: int, 
                                  alarm_count: int, 
                                  risk_score: float,
                                  alarms: List[dict]) -> dict:
        """Save/update a cached snapshot of alarm data for a location"""
        snapshot = {
            "lat": lat,
            "lon": lon,
            "lookback_days": lookback_days,
            "alarm_count": alarm_count,
            "risk_score": risk_score,
            "last_sync": datetime.utcnow(),
            "alarms": alarms
        }
        
        result = await self.db.alarm_snapshots.update_one(
            {
                "lat": lat,
                "lon": lon,
                "lookback_days": lookback_days
            },
            {"$set": snapshot},
            upsert=True
        )
        
        logger.info(f"Snapshot saved for ({lat}, {lon}): {alarm_count} alarms, risk={risk_score:.2f}")
        return snapshot
    
    async def get_alarm_snapshot(self, lat: float, lon: float, 
                                 lookback_days: int = 30) -> Optional[dict]:
        """Retrieve cached alarm snapshot for a location"""
        snapshot = await self.db.alarm_snapshots.find_one({
            "lat": lat,
            "lon": lon,
            "lookback_days": lookback_days
        })
        return snapshot
    
    async def count_alarms(self, lat: float, lon: float, 
                          lookback_days: int = 30,
                          radius_km: float = 50) -> int:
        """Count alarms in a geographic and time range"""
        cutoff_timestamp = int((datetime.utcnow() - timedelta(days=lookback_days)).timestamp())
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(np.cos(np.radians(lat)))) if lat != 0 else radius_km / 111.0
        
        count = await self.db.alarms.count_documents({
            "lat": {"$gte": lat - lat_delta, "$lte": lat + lat_delta},
            "lon": {"$gte": lon - lon_delta, "$lte": lon + lon_delta},
            "timestamp": {"$gte": cutoff_timestamp}
        })
        return count
    
    async def delete_old_alarms(self, days: int = 90):
        """Delete alarms older than N days"""
        cutoff_timestamp = int((datetime.utcnow() - timedelta(days=days)).timestamp())
        result = await self.db.alarms.delete_many({
            "timestamp": {"$lt": cutoff_timestamp}
        })
        logger.info(f"Deleted {result.deleted_count} alarms older than {days} days")
        return result.deleted_count
    
    async def get_stats(self) -> dict:
        """Get statistics about stored alarms"""
        alarm_count = await self.db.alarms.count_documents({})
        snapshot_count = await self.db.alarm_snapshots.count_documents({})
        
        return {
            "total_alarms": alarm_count,
            "total_snapshots": snapshot_count,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
mongodb_client: Optional[MongoDBClient] = None


async def get_mongodb_client() -> MongoDBClient:
    """Get or create MongoDB client"""
    global mongodb_client
    if mongodb_client is None:
        raise RuntimeError("MongoDB client not initialized")
    return mongodb_client
