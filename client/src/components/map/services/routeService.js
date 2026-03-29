
import { useRouteStore } from "../../zustand/store.js";
import { decodePolyline } from "../utils/polyline";
import timeStringToTimestamp from "../utils/timeStringToTimestamp";

/* global google */

export async function fetchRoute() {
  const { origin, destination, departureTime } = useRouteStore.getState();
  console.log("🗺️ fetchRoute called with:", { origin, destination, departureTime });

  return new Promise((resolve, reject) => {
    // Set a timeout of 10 seconds
    const timeout = setTimeout(() => {
      console.error("❌ fetchRoute timeout - no response from Google Maps after 10 seconds");
      reject(new Error("Timeout waiting for Google Maps response"));
    }, 10000);

    if (!origin || !destination || !departureTime) {
      clearTimeout(timeout);
      const missingFields = [];
      if (!origin) missingFields.push("origin");
      if (!destination) missingFields.push("destination");
      if (!departureTime) missingFields.push("departureTime");
      console.error("❌ Missing fields:", missingFields);
      return reject(new Error(`Missing route data: ${missingFields.join(", ")}`));
    }
    
    const timestamp = timeStringToTimestamp(departureTime);
    console.log("⏰ Converted timestamp:", timestamp);

    if (!window.google || !window.google.maps) {
      clearTimeout(timeout);
      console.error("❌ Google Maps API not loaded");
      reject(new Error("Google Maps API is not available"));
      return;
    }

    const directionsService = new google.maps.DirectionsService();
    console.log("🚗 DirectionsService created");

    directionsService.route(
      {
        origin,
        destination,
        travelMode: google.maps.TravelMode.DRIVING,
        drivingOptions: {
          departureTime: new Date(timestamp * 1000),
        },
      },
      (res, status) => {
        clearTimeout(timeout);
        
        if (status !== "OK") {
          console.error("❌ Directions request failed with status:", status);
          console.error("📋 Response:", res);
          return reject(new Error(`Directions request failed: ${status}`));
        }

        try {
          console.log("✅ Got response from DirectionsService");
          const coordinates = decodePolyline(res.routes[0].overview_polyline);
          console.log("📍 Decoded", coordinates.length, "coordinates from polyline");
          console.log("🔍 First coordinate:", coordinates[0]);
          console.log("🔍 Last coordinate:", coordinates[coordinates.length - 1]);
          
          const confines = [res.routes[0].legs[0].end_location, res.routes[0].legs[0].start_location]
          const duration = [res.routes[0].legs[0].duration.text]
          console.log("✅ Resolved with:", { coordinatesCount: coordinates.length, confines, duration });
          
          resolve({ coordinates, confines, duration });
        } catch (err) {
          clearTimeout(timeout);
          console.error("❌ Error parsing route:", err);
          reject(err);
        }
      }
    );
  });
}