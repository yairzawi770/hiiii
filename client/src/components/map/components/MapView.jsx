import { GoogleMap } from '@react-google-maps/api';

import RouteLayer from './RouteLayer.jsx';
import { useRouteStore } from '../../zustand/store.js';
import { useEffect, useRef } from 'react';

const ISRAEL_CENTER = { lat: 32.0853, lng: 34.7818 };
const ZOOM = 10;

const containerStyle = {
  width: '100%',
  height: '520px'
};

export default function MapView() {
  const segments = useRouteStore((s) => s.segments);
  const confines = useRouteStore((s) => s.confines)

  const mapRef = useRef(null);

  // פונקציה לשמירת הרפרנס של המפה
  const onLoad = map => {
    mapRef.current = map;
  };
  console.log(mapRef.current);

  // כאשר המסלול משתנה, נערוך רענון למרכז ולזום
  useEffect(() => {
    if (!mapRef.current) return;
    if (confines && confines.length >= 2) {

      // נקודות התחלה וסיום בלבד
      const start = confines[0];
      const end = confines[confines.length - 1];

      const bounds = new window.google.maps.LatLngBounds();
      bounds.extend(start);
      bounds.extend(end);

      mapRef.current.fitBounds(bounds, 100);

    } else {
      // אם אין מסלול – למרכז על ישראל
      mapRef.current.setCenter(ISRAEL_CENTER);
      mapRef.current.setZoom(ZOOM);
    }
  }, [confines]);

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={ISRAEL_CENTER}
      zoom={ZOOM}
      onLoad={onLoad}
    >
      <RouteLayer segments={segments} mapRef={mapRef} />
    </GoogleMap>
  );
}

