import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { fetchSentimentHistory } from '../api/client'

interface Props {
  ticker: string | null
}

export default function SentimentHistoryChart({ ticker }: Props) {
  const [days, setDays] = useState(30)

  const query = useQuery({
    queryKey: ['sentiment-history', ticker, days],
    queryFn: () => fetchSentimentHistory(ticker!, days),
    enabled: !!ticker,
    refetchInterval: 60000,
  })

  if (!ticker) return null

  const data = (query.data?.history ?? []).map((h) => ({
    date: new Date(h.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    composite: h.composite_score,
    bullish: h.bullish_count,
    bearish: h.bearish_count,
    neutral: h.neutral_count,
  }))

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">
          Sentiment Trend: <span className="font-mono text-blue-600">{ticker}</span>
        </h2>
        <div className="flex gap-1 text-sm">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={px-2 py-1 rounded }
            >
              {d}d
            </button>
          ))}
        </div>
      </div>
      {query.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      {data.length === 0 && !query.isLoading && (
        <p className="text-gray-400 text-sm">No history data yet — check back after the daily aggregation runs</p>
      )}
      {data.length > 0 && (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="compositeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" fontSize={10} />
            <YAxis domain={[-1, 1]} fontSize={10} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="composite" stroke="#3b82f6" fill="url(#compositeGrad)" strokeWidth={2} name="Composite Score" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
