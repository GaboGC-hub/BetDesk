export type Sport = 'basketball' | 'football' | 'tennis' | 'all'
export type AlertType = 'anomaly' | 'ev' | 'all'
export type MarketType = 'TOTAL' | 'SPREAD' | 'MONEYLINE' | '1X2' | 'BTTS' | 'all'

export interface Alert {
  id: number
  sport: Sport
  league: string
  event: string
  market: MarketType
  selection: string
  line?: number
  odds: number
  bookmaker: string
  reason: 'anomaly' | 'ev'
  score: number
  start_time_utc: string
  created_at_utc: string
  sent_at_utc: string | null
}

export interface AlertsResponse {
  alerts: Alert[]
  total: number
  page: number
  per_page: number
}

export interface DashboardStats {
  total: number
  evPositive: number
  anomalies: number
  sent: number
}

export interface FilterState {
  sport: Sport
  alertType: AlertType
  market: MarketType
  league: string
  sent: boolean | null
}
