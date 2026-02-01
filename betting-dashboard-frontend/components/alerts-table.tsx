'use client'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert } from '@/types'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { ExternalLink, TrendingUp, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'

interface AlertsTableProps {
  alerts: Alert[]
  isLoading?: boolean
}

const getSportIcon = (sport: string) => {
  switch (sport) {
    case 'basketball':
      return '🏀'
    case 'football':
      return '⚽'
    case 'tennis':
      return '🎾'
    default:
      return '🎯'
  }
}

const getReasonBadge = (reason: string, score: number) => {
  if (reason === 'ev') {
    return (
      <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">
        <TrendingUp className="mr-1 h-3 w-3" />
        EV+ {score.toFixed(1)}%
      </Badge>
    )
  }
  return (
    <Badge className="bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20">
      <AlertTriangle className="mr-1 h-3 w-3" />
      Z-score {score.toFixed(2)}
    </Badge>
  )
}

const getStatusBadge = (sentAt: string | null) => {
  if (sentAt) {
    return (
      <Badge variant="outline" className="border-green-500/50 text-green-500">
        <CheckCircle2 className="mr-1 h-3 w-3" />
        Enviada
      </Badge>
    )
  }
  return (
    <Badge variant="outline" className="border-yellow-500/50 text-yellow-500">
      <Clock className="mr-1 h-3 w-3" />
      Pendiente
    </Badge>
  )
}

export function AlertsTable({ alerts, isLoading }: AlertsTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-16 animate-pulse rounded-lg bg-card/50"
          />
        ))}
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/50 py-16">
        <div className="rounded-full bg-muted/50 p-4">
          <AlertTriangle className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="mt-4 text-lg font-semibold">No hay alertas disponibles</h3>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          El sistema está monitoreando eventos.
          <br />
          Las alertas aparecerán aquí cuando se detecten oportunidades.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border/40 bg-card/30 backdrop-blur-sm">
      <Table>
        <TableHeader>
          <TableRow className="border-border/40 hover:bg-transparent">
            <TableHead className="w-[100px]">Deporte</TableHead>
            <TableHead>Evento</TableHead>
            <TableHead>Mercado</TableHead>
            <TableHead>Cuota</TableHead>
            <TableHead>Bookmaker</TableHead>
            <TableHead>Análisis</TableHead>
            <TableHead>Inicio</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="text-right">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {alerts.map((alert) => (
            <TableRow
              key={alert.id}
              className="border-border/40 transition-colors hover:bg-muted/5"
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  <span className="text-xl">{getSportIcon(alert.sport)}</span>
                  <div className="flex flex-col">
                    <span className="text-xs font-medium capitalize">{alert.sport}</span>
                    <span className="text-xs text-muted-foreground">{alert.league}</span>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">{alert.event}</span>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(alert.created_at_utc), "d MMM 'a las' HH:mm", {
                      locale: es,
                    })}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{alert.market}</span>
                  <span className="text-xs text-muted-foreground">
                    {alert.selection} {alert.line ? `${alert.line}` : ''}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className="font-mono text-sm font-bold">
                  {alert.odds.toFixed(2)}
                </Badge>
              </TableCell>
              <TableCell>
                <span className="text-sm">{alert.bookmaker}</span>
              </TableCell>
              <TableCell>{getReasonBadge(alert.reason, alert.score)}</TableCell>
              <TableCell>
                <span className="text-sm">
                  {format(new Date(alert.start_time_utc), 'HH:mm', { locale: es })}
                </span>
              </TableCell>
              <TableCell>{getStatusBadge(alert.sent_at_utc)}</TableCell>
              <TableCell className="text-right">
                <Button variant="ghost" size="sm" className="h-8 w-8 bg-transparent p-0">
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
