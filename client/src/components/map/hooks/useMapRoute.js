
import { useCallback, useState } from 'react';
import { fetchRoute } from '../services/routeService.js';
import { submitTripDetails } from '../../../functions/tripSubmitService.js';
import { useRouteStore } from '../../zustand/store.js';
import timeStringToTimestamp from '../utils/timeStringToTimestamp.js';

export function useMapRoute() {
  const [loading, setLoading] = useState(false);
  const setSegments = useRouteStore((s) => s.setSegments);
  const setTripRisk = useRouteStore((s) => s.setTripRisk);
  const setDuration = useRouteStore((s) => s.setDuration);
  const setConfines = useRouteStore((s) => s.setConfines);

  const loadRoute = useCallback(async function loadRoute() {
    setLoading(true);
    try {
      console.log("📍 Starting route calculation with Google Maps...");
      setSegments([]);
      
      // Fetch actual route from Google Maps
      const routeData = await fetchRoute();
      const { coordinates, duration, confines } = routeData;
      console.log("✅ Got route with", coordinates.length, "coordinates");
      console.log("🔍 First coord format:", coordinates[0]);
      console.log("⏱️ Travel duration:", duration);
      console.log("📍 Confines:", confines);
      
      // Update store with duration and confines
      setDuration(duration[0]);
      setConfines(confines);
      
      // Coordinates from polyline decoder already have { lat, lon } format
      // No conversion needed - use them directly
      const coordsForBackend = coordinates;
      
      console.log("📤 Preparing payload for backend with", coordsForBackend.length, "coordinates");
      console.log("   Format check - first coord:", coordsForBackend[0]);
      
      // Get departure_time from store
      const storeState = useRouteStore.getState();
      const departure_time = timeStringToTimestamp(storeState.departureTime);
      
      const payload = { 
        coordinates: coordsForBackend, 
        departure_time 
      };
      
      console.log("📤 Sending to backend:", {
        coordCount: coordsForBackend.length,
        departure_time,
        firstCoord: coordsForBackend[0],
        lastCoord: coordsForBackend[coordsForBackend.length - 1]
      });
      
      // Submit to backend for risk calculation
      const response = await submitTripDetails(payload);
      console.log("📥 Response from backend:", response);
      
      // Backend returns snake_case: trip_risk
      const segments = response?.segments;
      const tripRisk = response?.trip_risk;
      
      if (!Array.isArray(segments)) {
        throw new Error(`Expected segments array, got: ${typeof segments}`);
      }

      // Convert backend segments to match frontend format if needed
      const segmentsForDisplay = segments.map(seg => ({
        coords: seg.coords || [],
        risk: seg.risk
      }));

      setTripRisk(tripRisk ?? null);
      setSegments(segmentsForDisplay);
      
      console.log("✅ SUCCESS!");
      console.log("   trip_risk:", tripRisk);
      console.log("   duration:", duration);
      console.log("   segments:", segmentsForDisplay.length);
    } catch (err) {
      console.error("❌ ERROR:", err.message);
      console.error("Full error:", err);
      setTripRisk(null);
      setSegments([]);
      setConfines(null);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setSegments, setTripRisk, setDuration, setConfines]);

  return { loading, loadRoute };
}
