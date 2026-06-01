import type { CityStats } from '../types'
import { RISK_BG, RISK_TEXT } from '../utils/riskColors'

interface StatsBarProps {
  stats: CityStats
}

export const StatsBar = ({ stats }: StatsBarProps) => {
  const badgeStyle = (bg: string, color: string) => ({
    background: bg,
    color,
    borderRadius: 999,
    padding: '4px 10px',
    fontSize: 12,
    fontWeight: 600,
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6
  })

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid #ddd',
        background: '#fff'
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 16 }}>DustWatch · Vadodara</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <div style={badgeStyle(RISK_BG.critical, RISK_TEXT.critical)}>
          Critical {stats.critical}
        </div>
        <div style={badgeStyle(RISK_BG.high, RISK_TEXT.high)}>
          High {stats.high}
        </div>
        <div style={badgeStyle(RISK_BG.medium, RISK_TEXT.medium)}>
          Medium {stats.medium}
        </div>
        <div style={badgeStyle(RISK_BG.low, RISK_TEXT.low)}>
          Low {stats.low}
        </div>
      </div>
      <div style={{ fontSize: 12, color: '#555', textAlign: 'right' }}>
        <div>Population exposed: {stats.populationExposed}</div>
        <div>Last updated: {new Date(stats.lastUpdated).toLocaleString()}</div>
      </div>
    </div>
  )
}
