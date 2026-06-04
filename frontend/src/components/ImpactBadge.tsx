interface ImpactBadgeProps {
  impact: string | null
}

export default function ImpactBadge({ impact }: ImpactBadgeProps) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    high: { bg: 'bg-red-100', text: 'text-red-800', label: 'HIGH' },
    medium: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'MEDIUM' },
    low: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'LOW' },
  }

  const c = config[impact ?? 'low'] ?? config.low

  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  )
}
