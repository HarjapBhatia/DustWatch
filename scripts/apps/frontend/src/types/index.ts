export type RiskLevel = 'critical' | 'high' | 'medium' | 'low'

export type PermitStatus = 'registered' | 'unregistered' | 'expired'

export interface ConstructionSite {
  id: string
  name: string
  coordinates: number[]
  polygon: number[][]
  riskLevel: RiskLevel
  riskScore: number
  permitStatus: PermitStatus
  areaM2: number
  activeDays: number
  nearbySchools: number
  nearbyHospitals: number
  detectedAt: string
  lastUpdated: string
  satelliteImageBefore?: string | null
  satelliteImageAfter?: string | null
  ward?: string | null
  address?: string | null
}

export interface CityStats {
  totalSites: number
  critical: number
  high: number
  medium: number
  low: number
  unregistered: number
  populationExposed: number
  lastUpdated: string
}
