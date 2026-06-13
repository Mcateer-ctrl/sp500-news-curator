import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import NewsFeed from '../components/NewsFeed'
import SentimentChart from '../components/SentimentChart'
import SentimentHistoryChart from '../components/SentimentHistoryChart'
import Watchlist from '../components/Watchlist'
import TickerFilter from '../components/TickerFilter'
import EarningsWidget from '../components/EarningsWidget'
import IndicatorsWidget from '../components/IndicatorsWidget'
import FedCalendarWidget from '../components/FedCalendarWidget'
import WhalesPanel from '../components/WhalesPanel'
import Card from '../components/Card'
import { fetchWatchlist } from '../api/client'

const RIGHT_TABS = [
  { key: 'sentiment', label: 'Sentiment' },
  { key: 'earnings', label: 'Earnings' },
  { key: 'indicators', label: 'Economy' },
  { key: 'fed', label: 'Fed' },
  { key: 'whales', label: 'Whales' },
] as const

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string>('sentiment')

  const { data: watchlistData } = useQuery({
    queryKey: ['watchlist'],
    queryFn: fetchWatchlist,
  })

  const tickers = (watchlistData?.watchlist ?? []).map((w) => w.ticker)

  return (
    <div className="px-4 lg:px-8">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6">
        {/* Left column — narrow sidebar */}
        <div className="lg:col-span-3 space-y-5">
          <Card padding="compact" hover={false}>
            <TickerFilter
              onTickerSelect={setSelectedTicker}
              selectedTicker={selectedTicker}
              availableTickers={tickers}
            />
          </Card>
          <Watchlist
            onTickerSelect={setSelectedTicker}
            selectedTicker={selectedTicker}
          />
        </div>

        {/* Center column — NewsFeed + optional history */}
        <div className="lg:col-span-6 space-y-5">
          <NewsFeed selectedTicker={selectedTicker} />
          {selectedTicker && (
            <SentimentHistoryChart ticker={selectedTicker} />
          )}
        </div>

        {/* Right column — Tabbed widgets */}
        <div className="lg:col-span-3">
          <Card padding="default" hover={false}>
            {/* Tab bar */}
            <div className="flex gap-1 mb-4 bg-stone-100 rounded-xl p-1">
              {RIGHT_TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 text-xs font-medium py-1.5 px-2 rounded-[0.625rem] transition-all duration-200 ${
                    activeTab === tab.key
                      ? 'bg-white text-stone-800 shadow-sm'
                      : 'text-stone-400 hover:text-stone-600'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="min-h-[300px]">
              {activeTab === 'sentiment' && (
                <SentimentChart selectedTicker={selectedTicker} />
              )}
              {activeTab === 'earnings' && (
                <EarningsWidget tickers={tickers} />
              )}
              {activeTab === 'indicators' && (
                <IndicatorsWidget />
              )}
              {activeTab === 'fed' && (
                <FedCalendarWidget />
              )}
              {activeTab === 'whales' && (
                <WhalesPanel />
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}