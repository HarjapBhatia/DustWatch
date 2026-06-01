import { MapContainer, TileLayer, Polygon, Popup } from 'react-leaflet'

import type { ConstructionSite } from '../types'
import { RISK_COLORS } from '../utils/riskColors'

interface MapViewProps {
  sites: ConstructionSite[]
  selectedId: string | null
  onSiteClick: (site: ConstructionSite) => void
}

const toLatLngs = (polygon: number[][] | number[][][]) => {
  const rings = Array.isArray(polygon[0][0]) ? (polygon as number[][][]) : [polygon as number[][]]
  return rings.map(ring => ring.map(([lng, lat]) => [lat, lng]))
}

export const MapView = ({ sites, selectedId, onSiteClick }: MapViewProps) => {
  return (
    <MapContainer
      center={[22.3072, 73.1812]}
      zoom={12}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
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
              weight: 2
            }}
            positions={positions}
            eventHandlers={{
              click: () => onSiteClick(site)
            }}
          >
            <Popup>
              <div style={{ fontSize: 12, fontWeight: 600 }}>{site.name}</div>
              <div style={{ fontSize: 12 }}>Risk score: {site.riskScore}</div>
            </Popup>
          </Polygon>
        )
      })}
    </MapContainer>
  )
}
