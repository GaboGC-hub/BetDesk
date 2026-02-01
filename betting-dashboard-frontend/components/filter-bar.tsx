'use client'

import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { FilterState, Sport, AlertType, MarketType } from '@/types'
import { X } from 'lucide-react'

interface FilterBarProps {
  filters: FilterState
  onFilterChange: (filters: FilterState) => void
  activeFiltersCount: number
}

const SPORT_OPTIONS: { value: Sport; label: string; emoji: string }[] = [
  { value: 'all', label: 'Todos los Deportes', emoji: '🎯' },
  { value: 'basketball', label: 'Basketball', emoji: '🏀' },
  { value: 'football', label: 'Football', emoji: '⚽' },
  { value: 'tennis', label: 'Tennis', emoji: '🎾' },
]

const ALERT_TYPE_OPTIONS: { value: AlertType; label: string }[] = [
  { value: 'all', label: 'Todos los Tipos' },
  { value: 'ev', label: 'Expected Value' },
  { value: 'anomaly', label: 'Anomalías' },
]

const MARKET_OPTIONS: { value: MarketType; label: string }[] = [
  { value: 'all', label: 'Todos los Mercados' },
  { value: 'TOTAL', label: 'Total Puntos' },
  { value: 'SPREAD', label: 'Spread' },
  { value: 'MONEYLINE', label: 'Moneyline' },
  { value: '1X2', label: '1X2' },
  { value: 'BTTS', label: 'Ambos Anotan' },
]

export function FilterBar({ filters, onFilterChange, activeFiltersCount }: FilterBarProps) {
  const resetFilters = () => {
    onFilterChange({
      sport: 'all',
      alertType: 'all',
      market: 'all',
      league: '',
      sent: null,
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">Filtros</h3>
          {activeFiltersCount > 0 && (
            <Badge variant="secondary" className="rounded-full">
              {activeFiltersCount} activos
            </Badge>
          )}
        </div>
        {activeFiltersCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={resetFilters}
            className="h-8 bg-transparent text-xs"
          >
            <X className="mr-1 h-3 w-3" />
            Limpiar filtros
          </Button>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Select
          value={filters.sport}
          onValueChange={(value: Sport) =>
            onFilterChange({ ...filters, sport: value })
          }
        >
          <SelectTrigger className="bg-card/50">
            <SelectValue placeholder="Deporte" />
          </SelectTrigger>
          <SelectContent>
            {SPORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                <span className="flex items-center gap-2">
                  <span>{option.emoji}</span>
                  <span>{option.label}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.alertType}
          onValueChange={(value: AlertType) =>
            onFilterChange({ ...filters, alertType: value })
          }
        >
          <SelectTrigger className="bg-card/50">
            <SelectValue placeholder="Tipo de Alerta" />
          </SelectTrigger>
          <SelectContent>
            {ALERT_TYPE_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.market}
          onValueChange={(value: MarketType) =>
            onFilterChange({ ...filters, market: value })
          }
        >
          <SelectTrigger className="bg-card/50">
            <SelectValue placeholder="Mercado" />
          </SelectTrigger>
          <SelectContent>
            {MARKET_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.sent === null ? 'all' : filters.sent ? 'sent' : 'pending'}
          onValueChange={(value) =>
            onFilterChange({
              ...filters,
              sent: value === 'all' ? null : value === 'sent',
            })
          }
        >
          <SelectTrigger className="bg-card/50">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="sent">Enviadas</SelectItem>
            <SelectItem value="pending">Pendientes</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
