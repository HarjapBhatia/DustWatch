import type { ConstructionSite } from '../types'
import { PERMIT_COLORS, RISK_BG, RISK_TEXT } from '../utils/riskColors'

interface SiteCardProps {
  site: ConstructionSite
  onClose: () => void
}

export const SiteCard = ({ site, onClose }: SiteCardProps) => {
  const shareSummary = async () => {
    const summary = [
      `Site: ${site.name}`,
      `Risk: ${site.riskLevel} (${site.riskScore})`,
      `Permit: ${site.permitStatus}`,
      `Area (m2): ${Math.round(site.areaM2)}`,
      `Active days: ${site.activeDays}`,
      `Detected at: ${site.detectedAt}`
    ].join('\n')

    try {
      await navigator.clipboard.writeText(summary)
      window.alert('Site summary copied to clipboard')
    } catch (error) {
      window.alert('Unable to copy to clipboard')
    }
  }

  return (
    <div style={{ padding: 16, background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{site.name}</div>
          <div style={{ fontSize: 12, color: '#555' }}>
            {site.ward ?? 'Ward N/A'} · {site.address ?? 'Address not available'}
          </div>
          <div style={{ fontSize: 12, color: '#555' }}>Detected: {site.detectedAt}</div>
          <div style={{ fontSize: 12, color: '#555', fontFamily: 'monospace' }}>
            {site.coordinates[0].toFixed(5)}, {site.coordinates[1].toFixed(5)}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}
        >
          Close
        </button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div
          style={{
            background: RISK_BG[site.riskLevel],
            color: RISK_TEXT[site.riskLevel],
            padding: '6px 10px',
            borderRadius: 6,
            fontWeight: 600,
            fontSize: 12
          }}
        >
          {site.riskLevel.toUpperCase()} · {site.riskScore}
        </div>
        <div
          style={{
            border: `1px solid ${PERMIT_COLORS[site.permitStatus]}`,
            color: PERMIT_COLORS[site.permitStatus],
            padding: '6px 10px',
            borderRadius: 6,
            fontWeight: 600,
            fontSize: 12
          }}
        >
          {site.permitStatus}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        <div style={{ background: '#f5f5f5', padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: 11, color: '#666' }}>Area (m2)</div>
          <div style={{ fontWeight: 600 }}>{Math.round(site.areaM2)}</div>
        </div>
        <div style={{ background: '#f5f5f5', padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: 11, color: '#666' }}>Active days</div>
          <div style={{ fontWeight: 600 }}>{site.activeDays}</div>
        </div>
        <div style={{ background: '#f5f5f5', padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: 11, color: '#666' }}>Nearby schools</div>
          <div style={{ fontWeight: 600 }}>{site.nearbySchools}</div>
        </div>
        <div style={{ background: '#f5f5f5', padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: 11, color: '#666' }}>Nearby hospitals</div>
          <div style={{ fontWeight: 600 }}>{site.nearbyHospitals}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button
          onClick={shareSummary}
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            border: '1px solid #333',
            background: '#fff',
            cursor: 'pointer'
          }}
        >
          Share violation
        </button>
        <button
          onClick={() => window.alert('Coming soon')}
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            border: '1px solid #333',
            background: '#fff',
            cursor: 'pointer'
          }}
        >
          Export evidence
        </button>
      </div>
    </div>
  )
}
