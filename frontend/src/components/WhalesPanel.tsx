import { useQuery } from '@tanstack/react-query'
import { fetchThirteenFFilings } from '../api/client'

const INSTITUTION_LABELS: Record<string, string> = {
  'BRK.B': 'Berkshire Hathaway',
  GS: 'Goldman Sachs',
  BLK: 'BlackRock',
}

interface Props {
  className?: string
}

export default function WhalesPanel({ className }: Props) {
  const query = useQuery({
    queryKey: ['13f-filings'],
    queryFn: () => fetchThirteenFFilings({ days: 90 }),
    refetchInterval: 600000,
  })

  const filings = query.data?.filings ?? []

  return (
    <div className={className}>
      <h2 className="text-lg font-semibold mb-3">Whale Watching (13F)</h2>
      {query.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      {filings.length === 0 && !query.isLoading && (
        <p className="text-gray-400 text-sm">No recent 13F filings found</p>
      )}
      <div className="space-y-2">
        {filings.map((f) => {
          const d = new Date(f.filing_date)
          const label = INSTITUTION_LABELS[f.ticker] || f.ticker
          return (
            <div key={f.id} className="flex items-center justify-between text-sm border-b border-gray-100 pb-1.5 last:border-0">
              <div>
                <span className="font-mono font-semibold">{f.ticker}</span>
                <span className="text-gray-400 text-xs ml-2">{label}</span>
              </div>
              <div className="text-right">
                <span className="text-gray-400 text-xs">
                  Filed: {d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
                {f.value !== null && (
                  <span className="ml-2 text-xs font-mono">
                    ${(f.value / 1e9).toFixed(1)}B
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
