import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { fetchTickerSentiment, fetchSectorSentiment } from '../api/client'

interface SentimentChartProps {
  selectedTicker: string | null
}

export default function SentimentChart({ selectedTicker }: SentimentChartProps) {
  const tickerQuery = useQuery({
    queryKey: ['sentiment-ticker', selectedTicker],
    queryFn: () => fetchTickerSentiment(selectedTicker!, 168),
    enabled: !!selectedTicker,
    refetchInterval: 60000,
  })

  const sectorQuery = useQuery({
    queryKey: ['sentiment-sectors'],
    queryFn: () => fetchSectorSentiment(24),
    enabled: !selectedTicker,
    refetchInterval: 60000,
  })

  if (selectedTicker) {
    const trend = tickerQuery.data?.sentiment_trend ?? []
    const chartData = trend.map((t) => ({
      hour: t.hour ? new Date(t.hour).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric' }) : '',
      Bullish: t.bullish_count,
      Bearish: t.bearish_count,
      Neutral: t.neutral_count,
    }))

    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3">
          Sentiment: <span className="font-mono text-blue-600">{selectedTicker}</span>
        </h2>
        {tickerQuery.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
        {chartData.length === 0 && !tickerQuery.isLoading && (
          <p className="text-gray-400 text-sm">No sentiment data for this ticker yet</p>
        )}
        {chartData.length > 0 && (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" fontSize={10} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="Bullish" stroke="#22c55e" strokeWidth={2} />
              <Line type="monotone" dataKey="Bearish" stroke="#ef4444" strokeWidth={2} />
              <Line type="monotone" dataKey="Neutral" stroke="#9ca3af" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    )
  }

  // No ticker selected — show sector summary
  const sectors = sectorQuery.data?.sectors ?? []

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-3">Sector Sentiment (24h)</h2>
      {sectorQuery.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      {sectors.length === 0 && !sectorQuery.isLoading && (
        <p className="text-gray-400 text-sm">No sector data yet</p>
      )}
      <div className="space-y-2">
        {sectors.map((s) => {
          const total = s.total || 1
          const bullPct = Math.round((s.bullish / total) * 100)
          const bearPct = Math.round((s.bearish / total) * 100)
          return (
            <div key={s.sector} className="text-sm">
              <div className="flex justify-between mb-0.5">
                <span className="font-medium">{s.sector}</span>
                <span className="text-gray-400">{s.total} articles</span>
              </div>
              <div className="flex h-2 rounded overflow-hidden bg-gray-100">
                <div className="bg-green-500" style={{ width: `${bullPct}%` }} />
                <div className="bg-red-500" style={{ width: `${bearPct}%` }} />
                <div className="bg-gray-300 flex-1" />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
