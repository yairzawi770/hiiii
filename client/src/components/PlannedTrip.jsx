import { useRouteStore } from './zustand/store.js'
import './TripForm.css'

export default function PlannedTrip({ onNewTrip } = {}) {
  const { origin, destination, departureTime, duration } = useRouteStore()

  return (
    <section className="planned-trip-bar">
      <div className="planned-trip-header">
        <div className="planned-trip-title">נסיעה מתוכננת</div>
        <button
          type="button"
          className="new-trip-button"
          onClick={onNewTrip}
        >
          נסיעה חדשה
        </button>
      </div>

      <div className="planned-trip-grid">
        <label className="planned-trip-field">
          <span className="planned-trip-label">מוצא</span>
          <input type="text" value={origin} readOnly />
        </label>

        <label className="planned-trip-field">
          <span className="planned-trip-label">יעד</span>
          <input type="text" value={destination} readOnly />
        </label>

        <label className="planned-trip-field">
          <span className="planned-trip-label">שעת יציאה</span>
          <input type="time" value={departureTime} readOnly />
        </label>

        <label className="planned-trip-field">
          <span className="planned-trip-label">זמן נסיעה</span>
          <input type="text" value={duration} readOnly placeholder="בהמשך…" />
        </label>
      </div>
    </section>
  )
}

