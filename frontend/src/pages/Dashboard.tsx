import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import NewsFeed from '../components/NewsFeed'
import SentimentChart from '../components/SentimentChart'
import Watchlist from '../components/Watchlist'
import TickerFilter from '../components/TickerFilter'
import { fetchWatchlist } from '../api/client'

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  const { data: watchlistData } = useQuery({
    queryKey: ['watchlist'],
    queryFn: fetchWatchlist,
  })

  const tickers = (watchlistData?.watchlist ?? []).map((w) => w.ticker)

  return (
    <div className="p-4 lg:p-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6">
        {/* Left column — Ticker filter + Watchlist */}
        <div className="lg:col-span-3 space-y-4">
          <TickerFilter
            onTickerSelect={setSelectedTicker}
            selectedTicker={selectedTicker}
            availableTickers={tickers}
          />
          <Watchlist
            onTickerSelect={setSelectedTicker}
            selectedTicker={selectedTicker}
          />
        </div>

        {/* Center column — News feed */}
        <div className="lg:col-span-6">
          <NewsFeed selectedTicker={selectedTicker} />
        </div>

        {/* Right column — Sentiment chart */}
        <div className="lg:col-span-3">
          <SentimentChart selectedTicker={selectedTicker} />
        </div>
      </div>
    </div>
  )
}
