//betting-dashboard-frontend/app/inicio/page.tsx
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import {
  Target,
  TrendingUp,
  Bell,
  BarChart3,
  Zap,
  Database,
  RefreshCw,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-primary/5">
      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-16">
        <div className="mx-auto max-w-4xl text-center">
          <Badge variant="secondary" className="mb-6 rounded-full px-4 py-1.5">
            <Zap className="mr-2 h-3 w-3" />
            Sistema Inteligente de Análisis de Apuestas Deportivas
          </Badge>
          <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              BetDesk
            </span>
          </h1>
          <p className="mb-8 text-xl text-muted-foreground sm:text-2xl">
            Detecta anomalías, calcula valor esperado y recibe alertas automáticas
            <br />
            de las mejores oportunidades en apuestas deportivas
          </p>
          <div className="flex flex-col justify-center gap-4 sm:flex-row">
            <Button asChild size="lg" className="gap-2">
              <Link href="/dashboard">
                Ver Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="gap-2 bg-transparent">
              <Link href="/alertas">
                Ver Alertas
                <Bell className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="border-border/40 bg-card/50 p-6 text-center backdrop-blur-sm">
            <Target className="mx-auto mb-3 h-8 w-8 text-primary" />
            <h3 className="text-3xl font-bold">3</h3>
            <p className="text-sm text-muted-foreground">Deportes</p>
            <p className="mt-1 text-xs text-muted-foreground">Basketball, Football, Tennis</p>
          </Card>
          <Card className="border-border/40 bg-card/50 p-6 text-center backdrop-blur-sm">
            <BarChart3 className="mx-auto mb-3 h-8 w-8 text-chart-2" />
            <h3 className="text-3xl font-bold">3</h3>
            <p className="text-sm text-muted-foreground">Mercados</p>
            <p className="mt-1 text-xs text-muted-foreground">Moneyline, Total, Spread</p>
          </Card>
          <Card className="border-border/40 bg-card/50 p-6 text-center backdrop-blur-sm">
            <TrendingUp className="mx-auto mb-3 h-8 w-8 text-chart-3" />
            <h3 className="text-3xl font-bold">2</h3>
            <p className="text-sm text-muted-foreground">Análisis</p>
            <p className="mt-1 text-xs text-muted-foreground">Anomalías + Expected Value</p>
          </Card>
          <Card className="border-border/40 bg-card/50 p-6 text-center backdrop-blur-sm">
            <Bell className="mx-auto mb-3 h-8 w-8 text-chart-4" />
            <h3 className="text-3xl font-bold">24/7</h3>
            <p className="text-sm text-muted-foreground">Alertas</p>
            <p className="mt-1 text-xs text-muted-foreground">Monitoreo en tiempo real</p>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-16">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">Como Funciona</h2>
          <p className="text-lg text-muted-foreground">
            Proceso automatizado de 4 pasos para detectar oportunidades
          </p>
        </div>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {[
            {
              step: '1',
              title: 'Scraping',
              description:
                'Extrae cuotas de Flashscore cada 10-30 minutos',
              icon: Database,
            },
            {
              step: '2',
              title: 'Análisis',
              description:
                'Detecta anomalías y calcula valor esperado (EV)',
              icon: BarChart3,
            },
            {
              step: '3',
              title: 'Alertas',
              description:
                'Envía notificaciones vía Telegram automáticamente',
              icon: Bell,
            },
            {
              step: '4',
              title: 'Dashboard',
              description:
                'Visualiza todas las oportunidades en tiempo real',
              icon: Target,
            },
          ].map((item) => (
            <Card
              key={item.step}
              className="relative overflow-hidden border-border/40 bg-card/50 p-6 backdrop-blur-sm"
            >
              <div className="absolute right-4 top-4 text-6xl font-bold text-primary/10">
                {item.step}
              </div>
              <div className="relative">
                <div className="mb-4 inline-flex rounded-full bg-primary/10 p-3">
                  <item.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-16">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Características Principales
          </h2>
          <p className="text-lg text-muted-foreground">
            Todo lo que necesitas para análisis profesional de apuestas
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[
            {
              title: 'Scraping Automático',
              description:
                'Extrae cuotas de múltiples bookmakers usando Playwright con anti-detección',
              icon: RefreshCw,
            },
            {
              title: 'Análisis Estadístico',
              description:
                'Modelos matemáticos para Basketball (Normal), Football (Poisson), Tennis (ELO)',
              icon: BarChart3,
            },
            {
              title: 'Detección de Anomalías',
              description:
                'Identifica cuotas outliers usando Z-score con umbral configurable',
              icon: TrendingUp,
            },
            {
              title: 'Expected Value (EV)',
              description:
                'Calcula el valor esperado de cada apuesta para maximizar ganancias',
              icon: Target,
            },
            {
              title: 'Alertas Telegram',
              description:
                'Notificaciones instantáneas cuando se detecta una oportunidad',
              icon: Bell,
            },
            {
              title: 'Base de Datos PostgreSQL',
              description:
                'Almacena eventos, cuotas y alertas históricas para análisis',
              icon: Database,
            },
          ].map((feature) => (
            <Card
              key={feature.title}
              className="border-border/40 bg-card/50 p-6 backdrop-blur-sm transition-all hover:border-primary/40"
            >
              <feature.icon className="mb-4 h-10 w-10 text-primary" />
              <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16">
        <Card className="border-primary/20 bg-gradient-to-br from-primary/10 via-card to-card p-12 text-center backdrop-blur-sm">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Comienza a Usar BetDesk
          </h2>
          <p className="mb-8 text-lg text-muted-foreground">
            Accede al dashboard para ver las alertas en tiempo real
          </p>
          <Button asChild size="lg" className="gap-2">
            <Link href="/dashboard">
              <CheckCircle2 className="h-5 w-5" />
              Ver Dashboard de Alertas
            </Link>
          </Button>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>BetDesk v1.0 - Sistema de Alertas de Apuestas Deportivas</p>
          <p className="mt-2">Usuario: admin | Contraseña: admin</p>
        </div>
      </footer>
    </div>
  )
}
