import { useState } from 'react'
import Card from './Card'

interface TickerFilterProps {
  onTickerSelect: (ticker: string | null) => void
  selectedTicker: string | null
  availableTickers: string[]
}

export default function TickerFilter({ onTickerSelect, selectedTicker, availableTickers }: TickerFilterProps) {
  const [search, setSearch] = useState('')

  const filtered = availableTickers.filter((t) =>
    t.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Card padding="default" hover={false}>
      <h2 className="text-lg font-semibold mb-3">Filter by Ticker</h2>
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search tickers..."
        className="w-full border border-stone-200 rounded-lg px-3 py-2 text-sm bg-surface-alt placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
      />
      <div className="space-y-1 max-h-64 overflow-y-auto mt-3">
        <button
          onClick={() => onTickerSelect(null)}
          className={`block w-full text-left px-2 py-1 rounded text-[0.8125rem] ${
            !selectedTicker ? 'text-accent bg-accent-light font-semibold' : 'text-stone-600 hover:bg-surface-hover'
          }`}
        >
          All Tickers
        </button>
        {filtered.map((ticker) => (
          <button
            key={ticker}
            onClick={() => onTickerSelect(ticker)}
            className={`block w-full text-left px-2 py-1 rounded text-[0.8125rem] font-mono ${
              selectedTicker === ticker ? 'text-accent bg-accent-light font-semibold' : 'text-stone-600 hover:bg-surface-hover'
            }`}
          >
            {ticker}
          </button>
        ))}
      </div>
    </Card>
  )
}
