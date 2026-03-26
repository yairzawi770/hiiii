from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AlarmRecord(BaseModel):
    """MongoDB alarm record model"""
    lat: float
    lon: float
    timestamp: int  # Unix timestamp when alarm occurred
    severity: Optional[str] = None  # e.g., "low", "medium", "high"
    category: Optional[str] = None  # e.g., "missile", "siren", etc.
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 32.0869,
                "lon": 34.7604,
                "timestamp": 1711449600,
                "severity": "high",
                "category": "missile",
                "description": "Missile alert in Tel Aviv area"
            }
        }


class AlarmSnapshot(BaseModel):
    """Cached aggregated alarm data for a location"""
    lat: float
    lon: float
    lookback_days: int = 30
    alarm_count: int = 0
    risk_score: float = 0.0
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    alarms: list = Field(default_factory=list)  # List of recent alarm records
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 32.0869,
                "lon": 34.7604,
                "lookback_days": 30,
                "alarm_count": 5,
                "risk_score": 0.5,
                "last_sync": "2026-03-26T12:00:00"
            }
        }
