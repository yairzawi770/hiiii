# MongoDB Data Storage

## Overview

The backend now stores alarm data in MongoDB with automatic synchronization from the RedAlert API every 5 minutes.

## Collections

### 1. `alarms` Collection

Stores individual alarm records fetched from RedAlert API.

**Schema:**
```json
{
  "_id": ObjectId,
  "lat": 32.0869,
  "lon": 34.7604,
  "timestamp": 1711449600,
  "severity": "high",
  "category": "missile",
  "description": "Missile alert in Tel Aviv area",
  "created_at": "2026-03-26T12:00:00Z",
  "updated_at": "2026-03-26T12:00:00Z"
}
```

**Indexes:**
- Compound index: (lat, lon, timestamp DESC)
- Single index: timestamp DESC
- TTL: Auto-delete after 90 days

### 2. `alarm_snapshots` Collection

Cached aggregated alarm data for specific locations.

**Schema:**
```json
{
  "_id": ObjectId,
  "lat": 32.0869,
  "lon": 34.7604,
  "lookback_days": 30,
  "alarm_count": 5,
  "risk_score": 0.5,
  "last_sync": "2026-03-26T12:00:00Z",
  "alarms": [
    {
      "lat": 32.0869,
      "lon": 34.7604,
      "timestamp": 1711449600,
      "severity": "high"
    }
  ]
}
```

**Indexes:**
- Compound unique index: (lat, lon, lookback_days)
- TTL: Auto-delete after 24 hours from last_sync

## Synchronization Process

### AlarmSyncTask

The backend runs a background task that:

1. **Runs every 5 minutes** (configurable via `SYNC_INTERVAL_MINUTES`)
2. **Fetches** recent alarms from RedAlert API (last 1 hour)
3. **Parses** alarm data and normalizes fields
4. **Stores** new alarms in MongoDB `alarms` collection
5. **Updates** alarm snapshots for queried locations

### Configuration

Environment variables in `docker-compose.yml`:

```env
MONGODB_URL=mongodb://mongodb:27017
SYNC_INTERVAL_MINUTES=5
```

## API Responses

### Trip Risk Endpoint

When calculating trip risk:

1. **First call**: Checks cache for alarm snapshots
2. **Cache hit** (< 1 hour old): Returns cached alarm data immediately
3. **Cache miss**: Queries API, stores result in DB for future use
4. **Risk calculation**: Uses cached data + route segments to compute final risk

**Benefits:**
- ⚡ **Fast**: Cached queries return instantly
- 💾 **Bandwidth**: Reduces API calls to RedAlert
- 📊 **Persistence**: Historical data available for analysis

## Maintenance

### Database Stats Endpoint

```bash
GET /api/db-stats
```

Returns:
```json
{
  "total_alarms": 12450,
  "total_snapshots": 342,
  "timestamp": "2026-03-26T12:30:00Z"
}
```

### Sync Status Endpoint

```bash
GET /api/sync-status
```

Returns:
```json
{
  "is_running": true,
  "last_sync": "2026-03-26T12:25:00Z",
  "sync_interval_minutes": 5
}
```

## Data Retention

- **Alarms**: Automatically deleted after 90 days
- **Snapshots**: Automatically deleted after 24 hours from last_sync
- **Manual cleanup**: Call delete_old_alarms(days=N) to manually clean up

## MongoDB Connection

### Local Development

```bash
docker-compose up mongodb
```

Connect via:
```bash
mongosh mongodb://localhost:27017/safe_travel
```

### Docker Compose

MongoDB runs automatically as a service in docker-compose with:
- Auto-initialization of `safe_travel` database
- Volume persistence: `mongodb_data`
- Healthcheck: Validates connectivity every 10 seconds

## Performance Optimization

1. **Indexes optimize**:
   - Location-based queries (lat, lon)
   - Time-range queries (timestamp)
   - Unique snapshots (lat, lon, lookback_days)

2. **TTL indexes auto-delete**:
   - Old alarms (90 days)
   - Stale snapshots (24 hours)

3. **Caching strategy**:
   - 1-hour cache for trip risk queries
   - Reduces API calls by ~90%
