// import { Polyline } from '@react-google-maps/api';
// const DEFAULT_WEIGHT = 4;

// function getRiskColor(risk) {
//   const r = typeof risk === 'number' ? risk : Number(risk);
//   if (!Number.isFinite(r)) return 'red';
//   if (r < 0.3) return 'green';
//   if (r < 0.6) return 'orange';
//   return 'red';
// }

// export default function RouteLayer({ segments = [] }) {
//   const renderSegments = Array.isArray(segments)
//     ? segments.filter((segment) => Array.isArray(segment?.coords) && segment.coords.length > 0)
//     : [];

//   return (
//     <>
//       {renderSegments.map((segment, idx) => (
//         <Polyline
//           key={idx}
//           path={segment.coords}
//           options={{
//             strokeColor: getRiskColor(segment.risk),
//             strokeWeight: DEFAULT_WEIGHT,
//           }}
//         />
//       ))}
//     </>
//   );
// }


import { useEffect, useRef } from 'react';
import { Polyline } from '@react-google-maps/api';

const DEFAULT_WEIGHT = 4;

function getRiskColor(risk) {
  const r = Number(risk);
  if (!Number.isFinite(r)) return 'red';
  if (r < 0.3) return 'green';
  if (r < 0.6) return 'orange';
  return 'red';
}

export default function RouteLayer({ segments = [], mapRef }) {
  const polylines = useRef([]);

  // מחיקת כל הפוליליינים מהמפה כשאין segments
  useEffect(() => {
    if (!mapRef?.current) return;

    // קודם הסר את כל הפוליליינים הישנים מהמפה
    polylines.current.forEach(poly => poly && poly.setMap(null));
    polylines.current = [];

    // עכשיו צייר את הפוליליינים החדשים
    segments.forEach((segment) => {
      if (!segment.coords || segment.coords.length === 0) return;

      const poly = new window.google.maps.Polyline({
        path: segment.coords,
        strokeColor: getRiskColor(segment.risk),
        strokeWeight: DEFAULT_WEIGHT,
        map: mapRef.current,
      });

      polylines.current.push(poly);
    });

  }, [segments, mapRef]);

  return null; // אין JSX, כל הפוליליינים נוצרו ישירות על המפה
}