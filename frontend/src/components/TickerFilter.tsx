import { useState } from 'react'

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
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-3">Filter by Ticker</h2>
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search tickers..."
        className="border rounded px-2 py-1 text-sm w-full mb-3"
      />
      <div className="space-y-1 max-h-64 overflow-y-auto">
        <button
          onClick={() => onTickerSelect(null)}
          className={`block w-full text-left px-2 py-1 rounded text-sm ${
            !selectedTicker ? 'bg-blue-50 font-semibold text-blue-700' : 'hover:bg-gray-50'
          }`}
        >
          All Tickers
        </button>
        {filtered.map((ticker) => (
          <button
            key={ticker}
            onClick={() => onTickerSelect(ticker)}
            className={`block w-full text-left px-2 py-1 rounded text-sm font-mono ${
              selectedTicker === ticker ? 'bg-blue-50 font-semibold text-blue-700' : 'hover:bg-gray-50'
            }`}
          >
            {ticker}
          </button>
        ))}
      </div>
    </div>
  )
}
