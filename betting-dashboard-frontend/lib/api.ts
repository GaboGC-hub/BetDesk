/**
 * API Service para conectar con el backend FastAPI
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Alert {
  id: string
  sport: string
  league: string
  match: string
  market: string
  line: number | null
  selection: string
  odds: number
  bookmaker: string
  message: string
  type: 'ev+' | 'anomalia'
  ev: number
  timestamp: string
  startTime: string | null
}

export interface Stats {
  totalAlertas: number
  alertasEV: number
  anomalias: number
  enviadas: number
  lastUpdate: string
}

export interface AlertsResponse {
  alerts: Alert[]
  total: number
  filters: {
    sport: string | null
    type: string | null
    limit: number
  }
}

export interface Sport {
  name: string
  count: number
}

/**
 * Obtiene las estadísticas generales del sistema
 */
export async function getStats(): Promise<Stats> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stats`)
    if (!response.ok) {
      throw new Error('Failed to fetch stats')
    }
    return await response.json()
  } catch (error) {
    console.error('Error fetching stats:', error)
    // Retornar datos por defecto en caso de error
    return {
      totalAlertas: 0,
      alertasEV: 0,
      anomalias: 0,
      enviadas: 0,
      lastUpdate: new Date().toISOString()
    }
  }
}

/**
 * Obtiene las alertas con filtros opcionales
 */
export async function getAlerts(
  sport?: string,
  alertType?: string,
  limit: number = 50
): Promise<AlertsResponse> {
  try {
    const params = new URLSearchParams()
    if (sport && sport !== 'todas') params.append('sport', sport)
    if (alertType && alertType !== 'todas') params.append('alert_type', alertType)
    params.append('limit', limit.toString())

    const response = await fetch(`${API_BASE_URL}/api/alerts?${params}`)
    if (!response.ok) {
      throw new Error('Failed to fetch alerts')
    }
    return await response.json()
  } catch (error) {
    console.error('Error fetching alerts:', error)
    return {
      alerts: [],
      total: 0,
      filters: {
        sport: sport || null,
        type: alertType || null,
        limit
      }
    }
  }
}

/**
 * Obtiene la lista de deportes disponibles
 */
export async function getSports(): Promise<Sport[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sports`)
    if (!response.ok) {
      throw new Error('Failed to fetch sports')
    }
    const data = await response.json()
    return data.sports
  } catch (error) {
    console.error('Error fetching sports:', error)
    return []
  }
}

/**
 * Health check del API
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`)
    return response.ok
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}
