import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

import type { ConstructionSite, RiskLevel } from '../types'
import type { Period, Pollutant } from '../App'
import { PERMIT_COLORS, RISK_COLORS } from '../utils/riskColors'

interface ZoneExposure {
  name: string
  wards: number[]
  zone_population: number
  pop_density_per_km2: number
  exposed_area_km2: number
  estimated_exposed: number
  exposure_pct: number
}

interface ExposureData {
  period: string
  pollutant: string
  threshold_ug_m3: number
  total_population: number
  total_exposed: number
  zones: ZoneExposure[]
  note: string
}

interface SidebarProps {
  sites: ConstructionSite[]
  selectedId: string | null
  onSelect: (site: ConstructionSite) => void
  period: Period
  pollutant: Pollutant
  onPeriodChange: (p: Period) => void
  onPollutantChange: (p: Pollutant) => void
}

type SidebarTab = 'sites' | 'exposure'
type FilterKey = 'all' | RiskLevel | 'unregistered'

const PERIOD_LABELS: Record<Period, string> = {
  oct_dec_2025: 'Oct–Dec 2025',
  jan_mar_2026: 'Jan–Mar 2026',
  apr_may_2026: 'Apr–May 2026',
}

const ZONE_COLORS: Record<string, string> = {
  'North Zone': '#3b82f6',
  'East Zone':  '#f59e0b',
  'West Zone':  '#10b981',
  'South Zone': '#ef4444',
}

function fmt(n: number) {
  return n.toLocaleString('en-IN')
}

export const Sidebar = ({
  sites, selectedId, onSelect,
  period, pollutant, onPeriodChange, onPollutantChange,
}: SidebarProps) => {
  const [tab, setTab] = useState<SidebarTab>('sites')
  const [filter, setFilter] = useState<FilterKey>('all')
  const [exposure, setExposure] = useState<ExposureData | null>(null)
  const [expLoading, setExpLoading] = useState(false)

  // Fetch exposure data whenever period, pollutant, or tab changes
  useEffect(() => {
    if (tab !== 'exposure') return
    setExpLoading(true)
    axios
      .get<ExposureData>(`/api/stats/population_exposure?period=${period}&pollutant=${pollutant}`)
      .then(r => { setExposure(r.data); setExpLoading(false) })
      .catch(() => setExpLoading(false))
  }, [period, pollutant, tab])

  const filteredSites = useMemo(() => {
    if (filter === 'all') return sites
    if (filter === 'unregistered') return sites.filter(s => s.permitStatus === 'unregistered')
    return sites.filter(s => s.riskLevel === filter)
  }, [filter, sites])

  const tabBtn = (label: string, value: SidebarTab) => (
    <button
      key={value}
      onClick={() => setTab(value)}
      style={{
        flex: 1, padding: '8px 4px', fontSize: 11, fontWeight: tab === value ? 700 : 400,
        border: 'none', borderBottom: tab === value ? '2px solid #3b82f6' : '2px solid transparent',
        background: 'transparent', cursor: 'pointer',
        color: tab === value ? '#3b82f6' : '#6b7280',
        transition: 'all 0.15s', letterSpacing: 0.3,
      }}
    >
      {label}
    </button>
  )

  const filterBtn = (label: string, value: FilterKey) => (
    <button
      key={value}
      onClick={() => setFilter(value)}
      style={{
        padding: '4px 8px', borderRadius: 5, border: '1px solid #d1d5db',
        background: filter === value ? '#e5e7eb' : '#fff',
        cursor: 'pointer', fontSize: 11,
      }}
    >
      {label}
    </button>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontFamily: 'system-ui, sans-serif' }}>

      {/* ── Period + pollutant controls ── */}
      <div style={{ padding: '10px 12px 0', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ fontSize: 10, color: '#9ca3af', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
          Period
        </div>
        <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
          {(Object.keys(PERIOD_LABELS) as Period[]).map(p => (
            <button
              key={p}
              onClick={() => onPeriodChange(p)}
              style={{
                flex: 1, fontSize: 10, padding: '4px 2px', borderRadius: 4,
                border: `1px solid ${period === p ? '#3b82f6' : '#d1d5db'}`,
                background: period === p ? '#eff6ff' : '#fff',
                color: period === p ? '#1d4ed8' : '#6b7280',
                cursor: 'pointer', fontWeight: period === p ? 700 : 400,
              }}
            >
              {PERIOD_LABELS[p]}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 6, marginBottom: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: 1 }}>Pollutant</span>
          {(['pm10', 'pm25'] as Pollutant[]).map(pol => (
            <button
              key={pol}
              onClick={() => onPollutantChange(pol)}
              style={{
                padding: '3px 10px', borderRadius: 4,
                border: `1px solid ${pollutant === pol ? '#f59e0b' : '#d1d5db'}`,
                background: pollutant === pol ? '#fef3c7' : '#fff',
                color: pollutant === pol ? '#92400e' : '#6b7280',
                fontWeight: pollutant === pol ? 700 : 400,
                cursor: 'pointer', fontSize: 11,
              }}
            >
              {pol.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab bar ── */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb' }}>
        {tabBtn('Sites', 'sites')}
        {tabBtn('Population Exposure', 'exposure')}
      </div>

      {/* ── Sites tab ── */}
      {tab === 'sites' && (
        <>
          <div style={{ padding: '8px 10px', display: 'flex', gap: 4, flexWrap: 'wrap', borderBottom: '1px solid #e5e7eb' }}>
            {filterBtn('All', 'all')}
            {filterBtn('Critical', 'critical')}
            {filterBtn('High', 'high')}
            {filterBtn('Medium', 'medium')}
            {filterBtn('Low', 'low')}
            {filterBtn('Unregistered', 'unregistered')}
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {filteredSites.length === 0 ? (
              <div style={{ padding: 12, fontSize: 12, color: '#6b7280' }}>No sites available.</div>
            ) : (
              filteredSites.map(site => {
                const isSelected = selectedId === site.id
                return (
                  <div
                    key={site.id}
                    onClick={() => onSelect(site)}
                    style={{
                      padding: 12, cursor: 'pointer',
                      borderLeft: `4px solid ${RISK_COLORS[site.riskLevel]}`,
                      background: isSelected ? '#f3f4f6' : '#fff',
                      borderBottom: '1px solid #f3f4f6',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{site.name}</div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 3 }}>Risk score: {site.riskScore}</div>
                    <div style={{ fontSize: 12, color: PERMIT_COLORS[site.permitStatus] }}>Permit: {site.permitStatus}</div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Active days: {site.activeDays}</div>
                  </div>
                )
              })
            )}
          </div>
        </>
      )}

      {/* ── Exposure tab ── */}
      {tab === 'exposure' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#374151', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Estimated population in modeled exposure zone
          </div>

          {expLoading && (
            <div style={{ fontSize: 12, color: '#9ca3af', padding: '20px 0', textAlign: 'center' }}>
              Computing exposure…
            </div>
          )}

          {!expLoading && exposure && (
            <>
              {/* Summary card */}
              <div style={{
                background: '#f8fafc', borderRadius: 8, padding: '12px 14px',
                border: '1px solid #e2e8f0', marginBottom: 14,
              }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: '#1e40af' }}>
                  {fmt(exposure.total_exposed)}
                </div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                  estimated residents in plume footprint
                </div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                  out of {fmt(exposure.total_population)} total ({((exposure.total_exposed / exposure.total_population) * 100).toFixed(1)}%)
                </div>
                <div style={{ fontSize: 10, color: '#cbd5e1', marginTop: 6 }}>
                  Threshold: {exposure.threshold_ug_m3} µg/m³ · {pollutant.toUpperCase()} · {PERIOD_LABELS[period as Period]}
                </div>
              </div>

              {/* Per-zone breakdown */}
              {exposure.zones.map(zone => {
                const color = ZONE_COLORS[zone.name] ?? '#6b7280'
                const barPct = Math.min(zone.exposure_pct, 100)
                return (
                  <div
                    key={zone.name}
                    style={{
                      marginBottom: 12, padding: '10px 12px',
                      background: '#fff', borderRadius: 7,
                      border: `1px solid #e5e7eb`,
                      borderLeft: `4px solid ${color}`,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                      <div style={{ fontWeight: 700, fontSize: 12, color: '#111827' }}>{zone.name}</div>
                      <div style={{ fontSize: 11, color: color, fontWeight: 700 }}>{zone.exposure_pct}%</div>
                    </div>

                    {/* Exposure bar */}
                    <div style={{ height: 5, background: '#f1f5f9', borderRadius: 3, marginBottom: 6, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${barPct}%`, background: color, borderRadius: 3 }} />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                      <div>
                        <span style={{ fontWeight: 600, color: '#1f2937' }}>{fmt(zone.estimated_exposed)}</span>
                        <span style={{ color: '#9ca3af' }}> exposed</span>
                      </div>
                      <div style={{ color: '#9ca3af' }}>{fmt(zone.zone_population)} total</div>
                    </div>

                    <div style={{ marginTop: 5, fontSize: 10, color: '#9ca3af' }}>
                      Wards {zone.wards.join(', ')} · {zone.exposed_area_km2} km² in plume
                    </div>
                  </div>
                )
              })}

              <div style={{ fontSize: 10, color: '#cbd5e1', lineHeight: 1.5, marginTop: 8, padding: '8px 0', borderTop: '1px solid #f1f5f9' }}>
                {exposure.note}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
