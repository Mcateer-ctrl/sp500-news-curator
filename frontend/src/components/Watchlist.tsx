import { useQuery } from '@tanstack/react-query'
import { fetchWatchlist, removeFromWatchlist, addToWatchlist, WatchlistItem } from '../api/client'
import { useState } from 'react'
import Card from './Card'

interface WatchlistProps {
  onTickerSelect: (ticker: string | null) => void
  selectedTicker: string | null
}

export default function Watchlist({ onTickerSelect, selectedTicker }: WatchlistProps) {
  const [newTicker, setNewTicker] = useState('')
  const { data, refetch } = useQuery({
    queryKey: ['watchlist'],
    queryFn: fetchWatchlist,
    refetchInterval: 60000,
  })

  const handleAdd = async () => {
    const ticker = newTicker.trim().toUpperCase()
    if (!ticker) return
    try {
      await addToWatchlist(ticker)
      setNewTicker('')
      refetch()
    } catch {
      // ignore duplicate errors
    }
  }

  const handleRemove = async (ticker: string) => {
    await removeFromWatchlist(ticker)
    if (selectedTicker === ticker) onTickerSelect(null)
    refetch()
  }

  const items = data?.watchlist ?? []

  return (
    <Card padding="default">
      <h2 className="text-lg font-semibold mb-3">Watchlist</h2>
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          placeholder="Add ticker..."
          className="border rounded px-2 py-1 text-sm flex-1"
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
        />
        <button
          onClick={handleAdd}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
        >
          Add
        </button>
      </div>
      <div className="space-y-1 max-h-96 overflow-y-auto">
        {items.map((item: WatchlistItem) => (
          <div
            key={item.id}
            className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer text-sm ${
              selectedTicker === item.ticker ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
            }`}
            onClick={() => onTickerSelect(selectedTicker === item.ticker ? null : item.ticker)}
          >
            <div>
              <span className="font-mono font-semibold">{item.ticker}</span>
              {item.sector && (
                <span className="text-gray-400 text-xs ml-2">{item.sector}</span>
              )}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleRemove(item.ticker)
              }}
              className="text-gray-400 hover:text-red-500 text-xs"
            >
              x
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-4">No tickers in watchlist</p>
        )}
      </div>
    </Card>
  )
}
