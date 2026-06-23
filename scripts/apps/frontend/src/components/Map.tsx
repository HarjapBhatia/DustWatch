import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Polygon, Popup, ImageOverlay, LayersControl, CircleMarker } from 'react-leaflet'
import axios from 'axios'

import type { ConstructionSite } from '../types'
import type { Period, Pollutant } from '../App'
import { RISK_COLORS } from '../utils/riskColors'

interface Wind { speed_m_s: number; direction_deg: number }

interface DustLayer {
  url: string
  bounds: [[number, number], [number, number]]
  wind: Wind | null
  legend: { min_ug_m3: number; max_ug_m3: number; label: string; citation: string }
}

interface AqiStation {
  uid: number
  lat: number
  lon: number
  aqi: number
  band: string
  color: string
  name: string
  time: string
}

interface MapViewProps {
  sites: ConstructionSite[]
  selectedId: string | null
  onSiteClick: (site: ConstructionSite) => void
  period: Period
  pollutant: Pollutant
}

const PERIOD_LABELS: Record<Period, string> = {
  oct_dec_2025: 'Oct–Dec 2025',
  jan_mar_2026: 'Jan–Mar 2026',
  apr_may_2026: 'Apr–May 2026',
}

const toLatLngs = (polygon: number[][] | number[][][]) => {
  const rings = Array.isArray(polygon[0][0]) ? (polygon as number[][][]) : [polygon as number[][]]
  return rings.map(ring => ring.map(([lng, lat]) => [lat, lng]))
}

function compassLabel(deg: number): string {
  const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
  return dirs[Math.round(deg / 22.5) % 16]
}

const WindArrow = ({ wind }: { wind: Wind }) => {
  const arrowDeg = (wind.direction_deg + 180) % 360
  return (
    <div style={{ textAlign: 'center', marginTop: 10 }}>
      <div style={{ fontSize: 10, color: '#aaa', marginBottom: 4, letterSpacing: 1, textTransform: 'uppercase' }}>Wind</div>
      <svg width={44} height={44} viewBox="0 0 44 44" style={{ display: 'block', margin: '0 auto' }}>
        <circle cx={22} cy={22} r={20} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
        <g transform={`rotate(${arrowDeg}, 22, 22)`}>
          <line x1={22} y1={34} x2={22} y2={10} stroke="#7dd3fc" strokeWidth={2} strokeLinecap="round" />
          <polygon points="22,6 18,14 26,14" fill="#7dd3fc" />
        </g>
      </svg>
      <div style={{ fontSize: 11, color: '#e2e8f0', marginTop: 4, fontWeight: 600 }}>
        {wind.speed_m_s.toFixed(1)} m/s
      </div>
      <div style={{ fontSize: 10, color: '#94a3b8' }}>
        {compassLabel(wind.direction_deg)} wind
      </div>
    </div>
  )
}

export const MapView = ({ sites, selectedId, onSiteClick, period, pollutant }: MapViewProps) => {
  const [dustLayer, setDustLayer] = useState<DustLayer | null>(null)
  const [loading, setLoading] = useState(false)
  const [aqiStations, setAqiStations] = useState<AqiStation[]>([])
  const abortRef = useRef<AbortController | null>(null)

  // Fetch AQI stations once on mount
  useEffect(() => {
    axios.get<{ stations: AqiStation[] }>('/api/layers/aqi_stations')
      .then(r => setAqiStations(r.data.stations))
      .catch(() => {})   // silently skip if token not yet set
  }, [])

  useEffect(() => {
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setLoading(true)
    axios
      .get<DustLayer>(`/api/layers/modeled_dust?period=${period}&pollutant=${pollutant}`, { signal: ctrl.signal })
      .then(r => { setDustLayer(r.data); setLoading(false) })
      .catch(e => { if (!axios.isCancel(e)) setLoading(false) })
  }, [period, pollutant])

  const overlayOpacity = loading ? 0.25 : 0.65
  const overlayUrl     = dustLayer?.url ?? ''
  const overlayBounds  = dustLayer?.bounds ?? [[22.25, 73.10], [22.45, 73.30]]

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer
        center={[22.3072, 73.1812]}
        zoom={12}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <LayersControl position="topright">
          <LayersControl.Overlay name="Modeled dust contribution" checked>
            <ImageOverlay
              url={overlayUrl}
              bounds={overlayBounds as [[number,number],[number,number]]}
              opacity={overlayOpacity}
            />
          </LayersControl.Overlay>

          <LayersControl.Overlay name="AQI monitoring stations" checked>
            <>
              {aqiStations.map(station => (
                <CircleMarker
                  key={station.uid}
                  center={[station.lat, station.lon]}
                  radius={14}
                  pathOptions={{
                    color: '#fff',
                    weight: 2,
                    fillColor: station.color,
                    fillOpacity: 0.9,
                  }}
                >
                  <Popup>
                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 4 }}>{station.name}</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: station.color }}>
                      AQI {station.aqi}
                    </div>
                    <div style={{ fontSize: 12, color: '#555', marginTop: 2 }}>{station.band}</div>
                    <div style={{ fontSize: 11, color: '#999', marginTop: 6 }}>
                      Updated: {station.time}
                    </div>
                    <div style={{ fontSize: 10, color: '#bbb', marginTop: 4 }}>
                      Source: WAQI / IQAir · Real measurement
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </>
          </LayersControl.Overlay>
        </LayersControl>

        {sites.map(site => {
          const isSelected = selectedId === site.id
          const positions = toLatLngs(site.polygon as number[][] | number[][][])
          return (
            <Polygon
              key={site.id}
              pathOptions={{
                color: RISK_COLORS[site.riskLevel],
                fillColor: RISK_COLORS[site.riskLevel],
                fillOpacity: isSelected ? 0.7 : 0.4,
                weight: 2,
              }}
              positions={positions}
              eventHandlers={{ click: () => onSiteClick(site) }}
            >
              <Popup>
                <div style={{ fontSize: 12, fontWeight: 600 }}>{site.name}</div>
                <div style={{ fontSize: 12 }}>Risk score: {site.riskScore}</div>
                <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
                  Estimated PM contribution from detected construction sites. Not a measurement.
                </div>
              </Popup>
            </Polygon>
          )
        })}
      </MapContainer>

      {/* Legend + wind arrow */}
      {dustLayer && (
        <div style={{
          position: 'absolute', bottom: 32, left: 12, zIndex: 1000,
          background: 'rgba(15,15,20,0.88)', borderRadius: 8, padding: '10px 14px',
          color: '#fff', fontSize: 12, minWidth: 210, pointerEvents: 'none',
          border: '1px solid rgba(255,255,255,0.12)',
        }}>
          <div style={{ fontWeight: 600, marginBottom: 2, fontSize: 11 }}>{dustLayer.legend.label}</div>
          <div style={{ fontSize: 10, color: '#64748b', marginBottom: 6 }}>
            {PERIOD_LABELS[period]} · Log scale
          </div>

          <div style={{
            height: 10, borderRadius: 4, marginBottom: 3,
            background: 'linear-gradient(to right, #440154, #3b528b, #21918c, #5ec962, #fde725)',
          }} />
          {pollutant === 'pm10'
            ? <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#94a3b8', marginBottom: 6 }}>
                <span>0.1</span><span>1</span><span>10+ µg/m³</span>
              </div>
            : <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#94a3b8', marginBottom: 6 }}>
                <span>0.025</span><span>0.25</span><span>2.5+ µg/m³</span>
              </div>
          }

          <div style={{ fontSize: 9, color: '#475569', fontStyle: 'italic' }}>
            Gaussian plume · EPA AP-42 · Briggs urban σ
          </div>
          <div style={{ fontSize: 9, color: '#334155', marginTop: 2 }}>
            Not a measurement — modeled estimate only
          </div>

          {dustLayer.wind && <WindArrow wind={dustLayer.wind} />}
        </div>
      )}
    </div>
  )
}
