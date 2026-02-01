//betting-dashboard-frontend/app/alertas/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FilterBar } from '@/components/filter-bar'
import { AlertsTable } from '@/components/alerts-table'
import { Alert, FilterState, DashboardStats } from '@/types'
import { RefreshCw, Bell, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function AlertasPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [filters, setFilters] = useState<FilterState>({
    sport: 'all',
    alertType: 'all',
    market: 'all',
    league: '',
    sent: null,
  })

  const [stats] = useState<DashboardStats>({
    total: 0,
    evPositive: 0,
    anomalies: 0,
    sent: 0,
  })

  // Simular carga de datos
  useEffect(() => {
    const loadAlerts = async () => {
      setIsLoading(true)
      // Aquí conectarías con tu API real: /api/alerts
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setAlerts([])
      setIsLoading(false)
      setLastUpdate(new Date())
    }

    loadAlerts()
  }, [filters])

  const handleRefresh = () => {
    setLastUpdate(new Date())
    // Aquí recargarías los datos
  }

  const activeFiltersCount = [
    filters.sport !== 'all',
    filters.alertType !== 'all',
    filters.market !== 'all',
    filters.league !== '',
    filters.sent !== null,
  ].filter(Boolean).length

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-primary/5">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Button
              asChild
              variant="ghost"
              size="sm"
              className="gap-2 bg-transparent"
            >
              <Link href="/dashboard">
                <ArrowLeft className="h-4 w-4" />
                Dashboard
              </Link>
            </Button>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Bell className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Alertas Recientes</h1>
                <p className="text-xs text-muted-foreground">
                  Última actualización: {lastUpdate.toLocaleTimeString('es')}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              <span className="text-sm text-muted-foreground">Sistema activo</span>
            </div>
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              className="gap-2 bg-transparent"
            >
              <RefreshCw className="h-4 w-4" />
              Actualizar
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Stats Summary */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-border/40 bg-card/50 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Alertas</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <Badge variant="outline" className="text-xs">
                Últimas 200
              </Badge>
            </div>
          </div>
          <div className="rounded-lg border border-border/40 bg-card/50 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Alertas EV+</p>
                <p className="text-2xl font-bold">{stats.evPositive}</p>
              </div>
              <Badge className="bg-green-500/10 text-xs text-green-500">
                Expected Value
              </Badge>
            </div>
          </div>
          <div className="rounded-lg border border-border/40 bg-card/50 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Anomalías</p>
                <p className="text-2xl font-bold">{stats.anomalies}</p>
              </div>
              <Badge className="bg-yellow-500/10 text-xs text-yellow-500">
                Cuotas Outliers
              </Badge>
            </div>
          </div>
          <div className="rounded-lg border border-border/40 bg-card/50 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Enviadas</p>
                <p className="text-2xl font-bold">{stats.sent}</p>
              </div>
              <Badge variant="outline" className="text-xs">
                Notificaciones Telegram
              </Badge>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6">
          <FilterBar
            filters={filters}
            onFilterChange={setFilters}
            activeFiltersCount={activeFiltersCount}
          />
        </div>

        {/* Alerts Table */}
        <div className="mb-8">
          <AlertsTable alerts={alerts} isLoading={isLoading} />
        </div>
      </main>
    </div>
  )
}
