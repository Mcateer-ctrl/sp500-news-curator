import { useQuery } from '@tanstack/react-query'
import { fetchEarnings } from '../api/client'

interface Props {
  tickers: string[]
}

export default function EarningsWidget({ tickers }: Props) {
  const query = useQuery({
    queryKey: ['earnings', tickers],
    queryFn: () => fetchEarnings({ upcoming: true, days: 14 }),
    refetchInterval: 300000,
  })

  const earnings = query.data?.earnings ?? []

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-3">Upcoming Earnings</h2>
      {query.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      {earnings.length === 0 && !query.isLoading && (
        <p className="text-gray-400 text-sm">No upcoming earnings for watched tickers</p>
      )}
      <div className="space-y-2">
        {earnings.map((e) => {
          const d = new Date(e.report_date)
          const hasActual = e.eps_actual !== null
          const beat = hasActual && e.eps_estimate !== null ? e.eps_actual! > e.eps_estimate! : null
          return (
            <div key={e.id} className="flex items-center justify-between text-sm border-b border-gray-100 pb-1.5 last:border-0">
              <div>
                <span className="font-mono font-semibold">{e.ticker}</span>
                <span className="text-gray-400 text-xs ml-2">
                  {d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  {e.report_time ? ` (${e.report_time})` : ''}
                </span>
              </div>
              <div className="text-right">
                {hasActual && beat !== null ? (
                  <span className={beat ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                    {beat ? 'Beat' : 'Miss'} {e.eps_actual?.toFixed(2)}
                  </span>
                ) : e.eps_estimate ? (
                  <span className="text-gray-500">Est: {e.eps_estimate.toFixed(2)}</span>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
