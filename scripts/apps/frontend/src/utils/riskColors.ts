import type { PermitStatus, RiskLevel } from '../types'

export const RISK_COLORS: Record<RiskLevel, string> = {
  critical: '#E24B4A',
  high: '#EF9F27',
  medium: '#378ADD',
  low: '#639922'
}

export const RISK_BG: Record<RiskLevel, string> = {
  critical: '#FCEBEB',
  high: '#FAEEDA',
  medium: '#E6F1FB',
  low: '#EAF3DE'
}

export const RISK_TEXT: Record<RiskLevel, string> = {
  critical: '#A32D2D',
  high: '#854F0B',
  medium: '#185FA5',
  low: '#3B6D11'
}

export const PERMIT_COLORS: Record<PermitStatus, string> = {
  registered: '#3B6D11',
  unregistered: '#A32D2D',
  expired: '#854F0B'
}
