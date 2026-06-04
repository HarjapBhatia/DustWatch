import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Polygon, Popup, ImageOverlay, LayersControl } from 'react-leaflet'
import axios from 'axios'

import type { ConstructionSite } from '../types'
import { RISK_COLORS } from '../utils/riskColors'

type Period = 'oct_dec_2025' | 'jan_mar_2026' | 'apr_may_2026'
type Pollutant = 'pm10' | 'pm25'

interface Wind { speed_m_s: number; direction_deg: number }

interface DustLayer {
  url: string
  bounds: [[number, number], [number, number]]
  wind: Wind | null
  period: Period
  pollutant: Pollutant
  legend: { min_ug_m3: number; max_ug_m3: number; label: string; citation: string; scale: string }
}

interface MapViewProps {
  sites: ConstructionSite[]
  selectedId: string | null
  onSiteClick: (site: ConstructionSite) => void
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
  // Meteorological direction = "coming FROM". Arrow points TO where wind goes = +180°.
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

export const MapView = ({ sites, selectedId, onSiteClick }: MapViewProps) => {
  const [period, setPeriod]     = useState<Period>('oct_dec_2025')
  const [pollutant, setPollutant] = useState<Pollutant>('pm10')
  const [dustLayer, setDustLayer] = useState<DustLayer | null>(null)
  const [loading, setLoading]   = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setLoading(true)
    axios
      .get<DustLayer>(`/api/layers/modeled_dust?period=${period}&pollutant=${pollutant}`, {
        signal: ctrl.signal,
      })
      .then(r => { setDustLayer(r.data); setLoading(false) })
      .catch(e => { if (!axios.isCancel(e)) setLoading(false) })
  }, [period, pollutant])

  const overlayOpacity = loading ? 0.25 : 0.65
  const overlayUrl     = dustLayer?.url ?? ''
  const overlayBounds  = dustLayer?.bounds ?? [[22.25, 73.10], [22.45, 73.30]]

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* ── Period + pollutant controls ── */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 1000,
        background: 'rgba(15,15,20,0.88)', borderRadius: 8, padding: '8px 12px',
        border: '1px solid rgba(255,255,255,0.12)', display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 }}>Period</div>
        <div style={{ display: 'flex', gap: 4 }}>
          {(Object.keys(PERIOD_LABELS) as Period[]).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              style={{
                fontSize: 11, padding: '3px 8px', borderRadius: 4, border: 'none', cursor: 'pointer',
                background: period === p ? '#3b82f6' : 'rgba(255,255,255,0.1)',
                color: period === p ? '#fff' : '#94a3b8',
                fontWeight: period === p ? 600 : 400,
                transition: 'all 0.15s',
              }}
            >
              {PERIOD_LABELS[p]}
            </button>
          ))}
        </div>

        <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1, marginTop: 2 }}>Pollutant</div>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['pm10', 'pm25'] as Pollutant[]).map(pol => (
            <button
              key={pol}
              onClick={() => setPollutant(pol)}
              style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 4, border: 'none', cursor: 'pointer',
                background: pollutant === pol ? '#f59e0b' : 'rgba(255,255,255,0.1)',
                color: pollutant === pol ? '#000' : '#94a3b8',
                fontWeight: pollutant === pol ? 700 : 400,
                transition: 'all 0.15s',
              }}
            >
              {pol.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

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
                  Estimated PM10 contribution from detected construction sites. Not a measurement.
                </div>
              </Popup>
            </Polygon>
          )
        })}
      </MapContainer>

      {/* ── Legend + wind arrow ── */}
      {dustLayer && (
        <div style={{
          position: 'absolute', bottom: 32, left: 12, zIndex: 1000,
          background: 'rgba(15,15,20,0.88)', borderRadius: 8, padding: '10px 14px',
          color: '#fff', fontSize: 12, minWidth: 210, pointerEvents: 'none',
          border: '1px solid rgba(255,255,255,0.12)',
        }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>{dustLayer.legend.label}</div>

          {/* Viridis gradient bar */}
          <div style={{
            height: 10, borderRadius: 4, marginBottom: 3,
            background: 'linear-gradient(to right, #440154, #3b528b, #21918c, #5ec962, #fde725)',
          }} />

          {/* Log-scale ticks */}
          {dustLayer.pollutant === 'pm10'
            ? <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#94a3b8', marginBottom: 8 }}>
                <span>0.1</span><span>1</span><span>10+ µg/m³</span>
              </div>
            : <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#94a3b8', marginBottom: 8 }}>
                <span>0.025</span><span>0.25</span><span>2.5+ µg/m³</span>
              </div>
          }

          <div style={{ fontSize: 10, color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.4 }}>
            Log scale · {dustLayer.legend.citation}
          </div>
          <div style={{ fontSize: 9, color: '#64748b', marginTop: 3 }}>
            Not a measurement — modeled estimate only
          </div>

          {dustLayer.wind && <WindArrow wind={dustLayer.wind} />}
        </div>
      )}
    </div>
  )
}
