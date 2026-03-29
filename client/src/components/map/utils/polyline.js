function decodeSignedNumber(value) {
  // Converts the encoded unsigned value into a signed delta.
  // See: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
  const shouldNegate = value & 1;
  const shifted = value >> 1;
  return shouldNegate ? ~shifted : shifted;
}

export function decodePolyline(encodedPolyline) {
  if (typeof encodedPolyline !== 'string') return [];
  if (encodedPolyline.length === 0) return [];

  let index = 0;
  let lat = 0;
  let lng = 0;
  const coordinates = [];

  while (index < encodedPolyline.length) {
    let result = 0;
    let shift = 0;
    let b;

    do {
      if (index >= encodedPolyline.length) return coordinates;
      b = encodedPolyline.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    lat += decodeSignedNumber(result);

    result = 0;
    shift = 0;

    do {
      if (index >= encodedPolyline.length) return coordinates;
      b = encodedPolyline.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    lng += decodeSignedNumber(result);

    coordinates.push({ lat: lat / 1e5, lon: lng / 1e5 });
  }

  return coordinates;
}

