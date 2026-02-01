//betting-dashboard-frontend/app/page.tsx
"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  TrendingUp, 
  AlertTriangle, 
  Send, 
  Activity,
  RefreshCw,
  Bell,
  BarChart3,
  Filter,
  Target
} from "lucide-react"

type FilterType = "todas" | "ev+" | "anomalias"
type SportType = "todas" | "basketball" | "football" | "tennis"

interface Alert {
  id: string
  sport: string
  type: "ev+" | "anomalia"
  match: string
  market: string
  odds: number
  ev: number
  timestamp: string
  bookmaker: string
}

export default function Dashboard() {
  const [activeFilter, setActiveFilter] = useState<FilterType>("todas")
  const [activeSport, setActiveSport] = useState<SportType>("todas")
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Mock data - replace with real data
  const stats = {
    totalAlertas: 0,
    alertasEV: 0,
    anomalias: 0,
    enviadas: 0,
    lastUpdate: new Date().toLocaleTimeString("es-ES")
  }

  const alerts: Alert[] = []

  const handleRefresh = () => {
    setIsRefreshing(true)
    // Simulate refresh
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const getFilteredAlerts = () => {
    return alerts.filter(alert => {
      const matchFilter = activeFilter === "todas" || alert.type === activeFilter
      const matchSport = activeSport === "todas" || alert.sport.toLowerCase() === activeSport
      return matchFilter && matchSport
    })
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                <Target className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">BetDesk</h1>
                <p className="text-xs text-muted-foreground">Sistema de Análisis de Apuestas</p>
              </div>
            </div>
            
            <nav className="hidden md:flex items-center gap-6">
              <Button variant="ghost" className="text-foreground">
                Dashboard
              </Button>
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Alertas
              </Button>
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Historial
              </Button>
            </nav>

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="icon"
                onClick={handleRefresh}
                className={isRefreshing ? "animate-spin" : ""}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button className="gap-2">
                <Bell className="h-4 w-4" />
                <span className="hidden sm:inline">Notificaciones</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <Card className="border-border bg-card hover:bg-card/80 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Alertas
              </CardTitle>
              <Activity className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{stats.totalAlertas}</div>
              <p className="text-xs text-muted-foreground mt-1">Últimas 200 apuestas</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card hover:bg-card/80 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Alertas EV+
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{stats.alertasEV}</div>
              <p className="text-xs text-muted-foreground mt-1">Expected Value Positivo</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card hover:bg-card/80 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Anomalías
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{stats.anomalias}</div>
              <p className="text-xs text-muted-foreground mt-1">Cuotas Outliers</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card hover:bg-card/80 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Enviadas
              </CardTitle>
              <Send className="h-4 w-4 text-info" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{stats.enviadas}</div>
              <p className="text-xs text-muted-foreground mt-1">Notificaciones Telegram</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters Section */}
        <Card className="border-border bg-card mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5 text-primary" />
              <CardTitle className="text-foreground">Filtros</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Alert Type Filters */}
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-3 block">
                  Tipo de Alerta
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={activeFilter === "todas" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveFilter("todas")}
                    className={activeFilter === "todas" ? "bg-primary" : ""}
                  >
                    Todas
                  </Button>
                  <Button
                    variant={activeFilter === "ev+" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveFilter("ev+")}
                    className={activeFilter === "ev+" ? "bg-success text-white hover:bg-success/90" : ""}
                  >
                    EV+
                  </Button>
                  <Button
                    variant={activeFilter === "anomalias" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveFilter("anomalias")}
                    className={activeFilter === "anomalias" ? "bg-warning text-white hover:bg-warning/90" : ""}
                  >
                    Anomalías
                  </Button>
                </div>
              </div>

              {/* Sport Filters */}
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-3 block">
                  Deporte
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={activeSport === "todas" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveSport("todas")}
                  >
                    Todas
                  </Button>
                  <Button
                    variant={activeSport === "basketball" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveSport("basketball")}
                    className="gap-2"
                  >
                    <span className="text-base">🏀</span>
                    Basketball
                  </Button>
                  <Button
                    variant={activeSport === "football" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveSport("football")}
                    className="gap-2"
                  >
                    <span className="text-base">⚽</span>
                    Football
                  </Button>
                  <Button
                    variant={activeSport === "tennis" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveSport("tennis")}
                    className="gap-2"
                  >
                    <span className="text-base">🎾</span>
                    Tennis
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alerts Section */}
        <Card className="border-border bg-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                <CardTitle className="text-foreground">Alertas Recientes</CardTitle>
              </div>
              <Button
                size="sm"
                onClick={handleRefresh}
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                Actualizar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {getFilteredAlerts().length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="mb-6 rounded-full bg-muted/50 p-6">
                  <Activity className="h-12 w-12 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  No hay alertas disponibles
                </h3>
                <p className="text-muted-foreground text-center max-w-md">
                  El sistema está monitoreando eventos en tiempo real. Las alertas aparecerán aquí cuando se detecten oportunidades de apuesta.
                </p>
                <div className="mt-6 flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                  Sistema activo
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {getFilteredAlerts().map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={alert.type === "ev+" ? "default" : "destructive"}>
                          {alert.type.toUpperCase()}
                        </Badge>
                        <span className="text-sm font-medium text-foreground">{alert.match}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {alert.market} - {alert.bookmaker}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-foreground">{alert.odds}</div>
                      <div className="text-sm text-success">+{alert.ev}% EV</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
