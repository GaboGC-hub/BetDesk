import { Card } from '@/components/ui/card'
import { type LucideIcon } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: number | string
  description: string
  icon: LucideIcon
  trend?: {
    value: number
    isPositive: boolean
  }
  colorClass?: string
}

export function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  colorClass = 'text-primary',
}: StatsCardProps) {
  return (
    <Card className="relative overflow-hidden border-border/40 bg-card/50 backdrop-blur-sm">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <h3 className="mt-2 text-3xl font-bold tracking-tight">{value}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            {trend && (
              <div className="mt-2 flex items-center gap-1">
                <span
                  className={`text-xs font-medium ${
                    trend.isPositive ? 'text-green-500' : 'text-red-500'
                  }`}
                >
                  {trend.isPositive ? '+' : ''}
                  {trend.value}%
                </span>
                <span className="text-xs text-muted-foreground">vs última hora</span>
              </div>
            )}
          </div>
          <div className={`rounded-full bg-primary/10 p-3 ${colorClass}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 h-1 w-full bg-gradient-to-r from-primary/20 via-primary/50 to-primary/20" />
    </Card>
  )
}
