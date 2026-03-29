const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org/search'

export async function searchIsraeliAddresses(query) {
  const trimmedQuery = query.trim()

  if (trimmedQuery.length < 2) {
    return []
  }

  const params = new URLSearchParams({
    format: 'jsonv2',
    addressdetails: '1',
    limit: '5',
    countrycodes: 'il',
    'accept-language': 'he',
    q: trimmedQuery,
  })

  try {
    const response = await fetch(`${NOMINATIM_BASE_URL}?${params.toString()}`)

    if (!response.ok) {
      return []
    }

    const data = await response.json()

    if (!Array.isArray(data)) {
      return []
    }

    return data.map((item) => ({
      id: item.place_id,
      label: item.display_name,
      lat: item.lat,
      lon: item.lon,
    }))
  } catch {
    return []
  }
}
