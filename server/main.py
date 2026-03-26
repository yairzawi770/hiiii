import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from schemas import TripRequest, TripRiskResponse
from risk_engine import RiskEngine
from alarm_service import AlarmService
from mongodb_client import MongoDBClient, mongodb_client
from alarm_sync import AlarmSyncTask, alarm_sync_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env variables
REDALERT_TOKEN = os.getenv("REDALERT_TOKEN", "pr_TwGtUQvnMgnWbYTRHOnwrGcKuZvDqppALWqwWdoJLSpfvsUYGNiyOfVwWoPBrOdr")
REDALERT_API_URL = os.getenv("REDALERT_API_URL", "https://redalert.orielhaim.com/api/stats/history")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "5"))

# Global instances
alarm_service = None
risk_engine = None
db_client = None
sync_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global alarm_service, risk_engine, db_client, sync_task, mongodb_client, alarm_sync_task
    
    logger.info("=" * 50)
    logger.info("🚀 Starting Safe Travel Backend...")
    logger.info("=" * 50)
    
    try:
        # Initialize MongoDB
        logger.info("📦 Connecting to MongoDB...")
        db_client = MongoDBClient(connection_url=MONGODB_URL)
        await db_client.connect()
        mongodb_client = db_client
        
        # Initialize AlarmService
        logger.info("🔔 Initializing AlarmService...")
        alarm_service = AlarmService(token=REDALERT_TOKEN, base_url=REDALERT_API_URL, mongodb_client=db_client)
        
        # Initialize RiskEngine
        logger.info("⚠️ Initializing RiskEngine...")
        risk_engine = RiskEngine(alarm_service=alarm_service)
        
        # Initialize and start AlarmSyncTask
        logger.info("🔄 Starting AlarmSyncTask...")
        sync_task = AlarmSyncTask(
            token=REDALERT_TOKEN,
            api_url=REDALERT_API_URL,
            mongodb_client=db_client,
            sync_interval_minutes=SYNC_INTERVAL_MINUTES
        )
        await sync_task.start()
        alarm_sync_task = sync_task
        
        logger.info("=" * 50)
        logger.info("✅ All services initialized successfully!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    if sync_task:
        await sync_task.stop()
    if db_client:
        await db_client.disconnect()
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="Safe Travel Backend",
    version="1.0.0",
    description="Trip risk analysis with real-time alarm integration",
    lifespan=lifespan
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    stats = await db_client.get_stats() if db_client else {"error": "DB not initialized"}
    sync_status = sync_task.get_status() if sync_task else {"error": "Sync task not initialized"}
    
    return {
        "status": "ok",
        "database": stats,
        "sync": sync_status
    }


@app.post("/api/trip-risk", response_model=TripRiskResponse)
async def calculate_trip_risk(request: TripRequest):
    """
    Calculate risk for a trip.
    
    Request:
        {
            "coordinates": [{"lat": 32.08..., "lon": 34.76...}, ...],
            "departure_time": 1711449600
        }
    
    Response:
        {
            "trip_risk": 0.45,
            "segments": [...],
            "checkpoints": [...],
            "metadata": {...}
        }
    """
    try:
        logger.info(f"Calculating trip risk for {len(request.coordinates)} coordinates")
        trip_risk, segments, checkpoints = await risk_engine.calculate_trip_risk(
            coordinates=request.coordinates,
            departure_time=request.departure_time
        )
        
        logger.info(f"Calculated trip risk: {trip_risk:.2%}")
        return TripRiskResponse(
            trip_risk=trip_risk,
            segments=segments,
            checkpoints=checkpoints,
            metadata={
                "total_points": len(request.coordinates),
                "departure_time": request.departure_time,
            }
        )
    except Exception as e:
        logger.error(f"Error calculating trip risk: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sync-status")
async def get_sync_status():
    """Get alarm sync task status"""
    if not sync_task:
        return {"error": "Sync task not initialized"}
    return sync_task.get_status()


@app.get("/api/db-stats")
async def get_database_stats():
    """Get database statistics"""
    if not db_client:
        return {"error": "Database not initialized"}
    return await db_client.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
