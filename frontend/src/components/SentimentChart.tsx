import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Area, ComposedChart,
} from 'recharts'
import { fetchTickerSentiment, fetchSectorSentiment } from '../api/client'

interface SentimentChartProps {
  selectedTicker: string | null
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white shadow-card border border-stone-100 rounded-lg px-3 py-2 text-xs">
      <p className="font-medium text-stone-600 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ backgroundColor: p.color }}
          />
          <span className="text-stone-500">{p.dataKey}:</span>
          <span className="font-semibold text-stone-800">{p.value}</span>
        </div>
      ))}
    </div>
  )
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
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-stone-800">
            <span className="font-mono text-accent text-base">{selectedTicker}</span>
          </h3>
          <span className="text-[0.6875rem] text-stone-400">7d sentiment</span>
        </div>
        {tickerQuery.isLoading && <p className="text-stone-400 text-xs">Loading...</p>}
        {chartData.length === 0 && !tickerQuery.isLoading && (
          <p className="text-stone-400 text-xs">No sentiment data yet</p>
        )}
        {chartData.length > 0 && (
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart data={chartData}>
              <defs>
                <linearGradient id="bullishGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="bearishGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="oklch(0.87 0 0)" strokeDasharray="none" vertical={false} />
              <XAxis dataKey="hour" fontSize={10} tick={{ fill: '#a8a29e' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} fontSize={10} tick={{ fill: '#a8a29e' }} axisLine={false} tickLine={false} width={24} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="Bullish" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Bearish" stroke="#ef4444" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="Bullish" fill="url(#bullishGrad)" stroke="none" />
              <Area type="monotone" dataKey="Bearish" fill="url(#bearishGrad)" stroke="none" />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    )
  }

  // No ticker selected — show sector summary (compact)
  const sectors = sectorQuery.data?.sectors ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-stone-800">Sector Sentiment</h3>
        <span className="text-[0.6875rem] text-stone-400">24h</span>
      </div>
      {sectorQuery.isLoading && <p className="text-stone-400 text-xs">Loading...</p>}
      {sectors.length === 0 && !sectorQuery.isLoading && (
        <p className="text-stone-400 text-xs">No sector data yet</p>
      )}
      <div className="space-y-2.5">
        {sectors.map((s) => {
          const total = s.total || 1
          const bullPct = Math.round((s.bullish / total) * 100)
          const bearPct = Math.round((s.bearish / total) * 100)
          const neutralPct = 100 - bullPct - bearPct
          return (
            <div key={s.sector} className="text-xs">
              <div className="flex justify-between mb-1">
                <span className="font-medium text-stone-700">{s.sector}</span>
                <span className="text-stone-400">{s.total} articles</span>
              </div>
              <div className="flex h-1.5 rounded-full overflow-hidden bg-stone-100">
                <div
                  className="bg-emerald-500 rounded-full"
                  style={{ width: ${bullPct}% }}
                />
                <div
                  className="bg-red-500 rounded-full"
                  style={{ width: ${bearPct}% }}
                />
                <div
                  className="bg-stone-200 rounded-full"
                  style={{ width: ${neutralPct}% }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
