import MapView from "../src/components/map/components/MapView"
import './App.css'
import { useState } from 'react'
import TripForm from './components/TripForm'
import PlannedTrip from './components/PlannedTrip'
import { useRouteStore } from './components/zustand/store.js'
import RiskMessage from './components/RiskMessage'

function App() {
  const [isPlanned, setIsPlanned] = useState(false)
  const [mapKey, setMapKey] = useState(0)
  const resetRoute = useRouteStore((s) => s.reset)
  const setSegments = useRouteStore((s) => s.setSegments)
  const tripRisk = useRouteStore((s) => s.tripRisk)

  return (
    <main className="app">
      {/* <div className="map-layout">
        <div className="map-shell">
          <MapView />
          
        </div>
      </div> */}

      <div className="planned-layout">
        <div className="planned-right">
          <div className="map-shell">
            <MapView />
            {!isPlanned && (
              <div className="planner-overlay">
                <TripForm onPlanned={() => setIsPlanned(true)} />
              </div>
            )}
            {isPlanned && (
              <div className="planner-topbar">
                <PlannedTrip
                  onNewTrip={() => {
                    resetRoute()
                    setSegments([])
                    setIsPlanned(false)
                  }}
                />
              </div>
            )}
          </div>
        </div>
        {isPlanned && (
          <aside className="planned-left">
            <section className="risk-panel">
              <div className="risk-panel-title">רמת סיכון לנסיעה</div>
              <RiskMessage riskValue={tripRisk} />
            </section>
          </aside>
        )
        }
      </div>

    </main>
  )
}

export default App
