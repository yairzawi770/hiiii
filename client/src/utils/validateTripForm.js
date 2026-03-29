export function validateTripForm({
  origin,
  destination,
  departureTime,
  selectedOrigin,
  selectedDestination,
}) {
  const trimmedOrigin = origin.trim();
  const trimmedDestination = destination.trim();

  if (!trimmedOrigin || !trimmedDestination || !departureTime) {
    return 'יש למלא מוצא, יעד ושעת יציאה לפני שליחה.';
  }

  if (!selectedOrigin || !selectedDestination) {
    return 'כדי לתכנן נסיעה, יש לבחור מוצא ויעד מתוך רשימת ההצעות.';
  }

  const originLat = Number(selectedOrigin.lat);
  const originLon = Number(selectedOrigin.lon);
  const destinationLat = Number(selectedDestination.lat);
  const destinationLon = Number(selectedDestination.lon);

  if (
    !Number.isFinite(originLat) ||
    !Number.isFinite(originLon) ||
    !Number.isFinite(destinationLat) ||
    !Number.isFinite(destinationLon)
  ) {
    return 'חסרים נתוני מפה תקינים (lat/lon). בחר מחדש כתובות מהרשימה.';
  }

  return null;
}