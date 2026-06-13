interface ImpactBadgeProps {
  impact: string | null
}

export default function ImpactBadge({ impact }: ImpactBadgeProps) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    high: { bg: 'bg-red-50', text: 'text-red-700', label: 'HIGH' },
    medium: { bg: 'bg-amber-50', text: 'text-amber-700', label: 'MED' },
    low: { bg: 'bg-stone-100', text: 'text-stone-500', label: 'LOW' },
  }

  const c = config[impact ?? 'low'] ?? config.low

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[0.625rem] font-bold tracking-wide ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  )
}
