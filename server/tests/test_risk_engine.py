import pytest
from unittest.mock import AsyncMock, MagicMock
from schemas import Point
from risk_engine import RiskEngine
from alarm_service import AlarmService


@pytest.fixture
def mock_alarm_service():
    """Create a mock AlarmService."""
    service = AsyncMock(spec=AlarmService)
    service.get_alarm_history = AsyncMock(return_value={
        "alarm_count": 2,
        "risk_score": 0.2
    })
    return service


@pytest.fixture
def risk_engine(mock_alarm_service):
    """Create RiskEngine with mock AlarmService."""
    return RiskEngine(alarm_service=mock_alarm_service)


@pytest.mark.asyncio
async def test_interpolate_point(risk_engine):
    """Test point interpolation at midpoint."""
    coords = [Point(lat=32.0, lon=34.0), Point(lat=32.2, lon=34.2)]
    mid = risk_engine._interpolate_point(coords, 0.5)
    assert abs(mid.lat - 32.1) < 0.01
    assert abs(mid.lon - 34.1) < 0.01


@pytest.mark.asyncio
async def test_interpolate_point_start(risk_engine):
    """Test point interpolation at start."""
    coords = [Point(lat=32.0, lon=34.0), Point(lat=32.2, lon=34.2)]
    start = risk_engine._interpolate_point(coords, 0.0)
    assert start.lat == 32.0
    assert start.lon == 34.0


@pytest.mark.asyncio
async def test_interpolate_point_end(risk_engine):
    """Test point interpolation at end."""
    coords = [Point(lat=32.0, lon=34.0), Point(lat=32.2, lon=34.2)]
    end = risk_engine._interpolate_point(coords, 1.0)
    assert end.lat == 32.2
    assert end.lon == 34.2


@pytest.mark.asyncio
async def test_calculate_trip_risk(risk_engine):
    """Test full trip risk calculation."""
    coords = [
        Point(lat=32.0, lon=34.0),
        Point(lat=32.05, lon=34.05),
        Point(lat=32.1, lon=34.1),
        Point(lat=32.15, lon=34.15),
        Point(lat=32.2, lon=34.2),
    ]
    trip_risk, segments, checkpoints = await risk_engine.calculate_trip_risk(
        coordinates=coords,
        departure_time=1711449600
    )
    
    assert 0.0 <= trip_risk <= 1.0
    assert len(segments) == 4
    assert len(checkpoints) == 5
    
    # Check checkpoint types
    checkpoint_types = [cp.checkpoint_type for cp in checkpoints]
    assert "origin" in checkpoint_types
    assert "destination" in checkpoint_types
    assert "midpoint_25" in checkpoint_types
    assert "midpoint_50" in checkpoint_types
    assert "midpoint_75" in checkpoint_types


@pytest.mark.asyncio
async def test_calculate_trip_risk_insufficient_points(risk_engine):
    """Test that error is raised with insufficient points."""
    coords = [Point(lat=32.0, lon=34.0)]
    with pytest.raises(ValueError):
        await risk_engine.calculate_trip_risk(
            coordinates=coords,
            departure_time=1711449600
        )
