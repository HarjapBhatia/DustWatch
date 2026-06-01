import { useMemo, useState } from 'react'

import type { ConstructionSite, RiskLevel } from '../types'
import { PERMIT_COLORS, RISK_COLORS } from '../utils/riskColors'

interface SidebarProps {
  sites: ConstructionSite[]
  selectedId: string | null
  onSelect: (site: ConstructionSite) => void
}

type FilterKey = 'all' | RiskLevel | 'unregistered'

export const Sidebar = ({ sites, selectedId, onSelect }: SidebarProps) => {
  const [filter, setFilter] = useState<FilterKey>('all')

  const filteredSites = useMemo(() => {
    if (filter === 'all') {
      return sites
    }

    if (filter === 'unregistered') {
      return sites.filter(site => site.permitStatus === 'unregistered')
    }

    return sites.filter(site => site.riskLevel === filter)
  }, [filter, sites])

  const filterButton = (label: string, value: FilterKey) => (
    <button
      key={value}
      onClick={() => setFilter(value)}
      style={{
        padding: '6px 10px',
        borderRadius: 6,
        border: '1px solid #ccc',
        background: filter === value ? '#eee' : '#fff',
        cursor: 'pointer',
        fontSize: 12
      }}
    >
      {label}
    </button>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {filterButton('All', 'all')}
        {filterButton('Critical', 'critical')}
        {filterButton('High', 'high')}
        {filterButton('Medium', 'medium')}
        {filterButton('Low', 'low')}
        {filterButton('Unregistered', 'unregistered')}
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {filteredSites.length === 0 ? (
          <div style={{ padding: 12, fontSize: 12, color: '#666' }}>
            No sites available yet.
          </div>
        ) : (
          filteredSites.map(site => {
            const isSelected = selectedId === site.id
            return (
              <div
                key={site.id}
                onClick={() => onSelect(site)}
                style={{
                  padding: 12,
                  cursor: 'pointer',
                  borderLeft: `4px solid ${RISK_COLORS[site.riskLevel]}`,
                  background: isSelected ? '#f2f2f2' : '#fff',
                  borderBottom: '1px solid #eee'
                }}
              >
                <div style={{ fontWeight: 600 }}>{site.name}</div>
                <div style={{ fontSize: 12, color: '#555', marginTop: 4 }}>
                  Risk score: {site.riskScore}
                </div>
                <div style={{ fontSize: 12, color: PERMIT_COLORS[site.permitStatus] }}>
                  Permit: {site.permitStatus}
                </div>
                <div style={{ fontSize: 12, color: '#777' }}>
                  Active days: {site.activeDays}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
