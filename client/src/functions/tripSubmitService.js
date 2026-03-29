const TRIP_SUBMIT_URL = 'http://localhost:8000/api/trip-risk'

// Temporary mock toggle (set to false when backend is ready)
const USE_MOCK = false

function clamp01(n) {
  if (!Number.isFinite(n)) return 0
  return Math.max(0, Math.min(1, n))
}

function buildMockSegments(coordinates = []) {
  if (!Array.isArray(coordinates)) return []
  if (coordinates.length < 2) return []

  const segments = []

  // Create a simple gradient "risk zones" along the route length.
  // risk: 0.05..0.95 with some deterministic variation.
  const denom = Math.max(1, coordinates.length - 2)
  for (let i = 0; i < coordinates.length - 1; i += 1) {
    const a = coordinates[i]
    const b = coordinates[i + 1]
    if (!a || !b) continue

    const t = denom === 0 ? 0 : i / denom
    const base = 0.05 + 0.9 * t
    const wave = 0.1 * Math.sin(t * Math.PI * 4) // deterministic wave
    const risk = clamp01(base + wave)

    segments.push({
      coords: [a, b],
      risk,
    })
  }

  return segments
}

async function mockSubmitTripDetails(payload) {
  // Simulate network latency (500-1000ms).
  const delayMs = 500 + Math.floor(Math.random() * 501)
  await new Promise((r) => setTimeout(r, delayMs))

  const coordinates = payload?.coordinates
  const segments = buildMockSegments(coordinates)
  const tripRisk = segments.length > 0 
    ? segments.reduce((sum, s) => sum + s.risk, 0) / segments.length 
    : 0.25
  
  return { 
    segments,
    tripRisk,
    checkpoints: []
  }
}

async function realSubmitTripDetails(payload) {
  if (!TRIP_SUBMIT_URL) {
    throw new Error('יש להגדיר URL בקובץ tripSubmitService.js לפני שליחה לשרת.')
  }

  console.log("🔵 ============ realSubmitTripDetails ============");
  console.log("🔵 URL:", TRIP_SUBMIT_URL);
  console.log("🔵 Payload:", JSON.stringify(payload, null, 2));
  
  try {
    console.log("🟡 Starting fetch...");
    
    const controller = new AbortController();
    const timeout = setTimeout(() => {
      console.error("🔴 TIMEOUT - aborting fetch after 15 seconds");
      controller.abort();
    }, 15000);

    const response = await fetch(TRIP_SUBMIT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    clearTimeout(timeout);
    console.log("🟢 Fetch completed, status:", response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error("🔴 Response NOT ok:");
      console.error("  Status:", response.status);
      console.error("  Body:", errorText);
      throw new Error(`Status ${response.status}: ${errorText}`)
    }

    const data = await response.json();
    console.log("🟢 Parsed JSON response:", data);
    return data;
  } catch (err) {
    console.error("🔴 FETCH ERROR:", err.name, err.message);
    if (err.name === 'AbortError') {
      throw new Error("Timeout - server did not respond in 15 seconds");
    }
    throw err;
  }
}

export async function submitTripDetails(payload) {
  if (USE_MOCK) return mockSubmitTripDetails(payload)
  return realSubmitTripDetails(payload)
}
