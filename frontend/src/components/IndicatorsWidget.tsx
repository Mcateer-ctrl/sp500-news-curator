import { useQuery } from '@tanstack/react-query'
import { fetchIndicators } from '../api/client'

const LABELS: Record<string, string> = {
  cpi: 'CPI',
  nonfarm_payrolls: 'Nonfarm Payrolls',
  unemployment_rate: 'Unemployment Rate',
  fed_funds_rate: 'Fed Funds Rate',
  gdp: 'GDP',
}

const FORMAT: Record<string, (v: number) => string> = {
  cpi: (v) => v.toFixed(1) + '%',
  nonfarm_payrolls: (v) => v.toLocaleString(),
  unemployment_rate: (v) => v.toFixed(1) + '%',
  fed_funds_rate: (v) => v.toFixed(2) + '%',
  gdp: (v) => v.toFixed(1) + '%',
}

export default function IndicatorsWidget() {
  const query = useQuery({
    queryKey: ['indicators'],
    queryFn: () => fetchIndicators('cpi,nonfarm_payrolls,unemployment_rate,fed_funds_rate,gdp', 90),
    refetchInterval: 300000,
  })

  const indicators = query.data?.indicators ?? {}

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-3">Economic Indicators</h2>
      {query.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      {Object.keys(indicators).length === 0 && !query.isLoading && (
        <p className="text-gray-400 text-sm">No indicator data yet</p>
      )}
      <div className="space-y-3">
        {Object.entries(indicators).map(([name, values]) => {
          const latest = values[0]
          const prev = values[1]
          if (!latest) return null
          const diff = prev ? latest.value - prev.value : 0
          const isPositive = diff >= 0
          return (
            <div key={name} className="text-sm">
              <div className="flex justify-between items-center">
                <span className="font-medium">{LABELS[name] || name}</span>
                <div className="text-right">
                  <span className="font-mono font-semibold">{FORMAT[name] ? FORMAT[name](latest.value) : latest.value}</span>
                  {prev && (
                    <span className={isPositive ? 'text-green-600 text-xs ml-2' : 'text-red-600 text-xs ml-2'}>
                      {isPositive ? '▲' : '▼'} {FORMAT[name] ? FORMAT[name](Math.abs(diff)) : ''}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex h-1.5 gap-0.5 mt-1">
                {values.slice().reverse().map((v, i) => {
                  const max = Math.max(...values.map((x) => x.value))
                  const min = Math.min(...values.map((x) => x.value))
                  const pct = max !== min ? (v.value - min) / (max - min) : 0.5
                  return (
                    <div
                      key={i}
                      className="flex-1 bg-blue-500 rounded-sm"
                      style={{ opacity: 0.3 + 0.7 * pct, height: '100%' }}
                    />
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
