import { useQuery } from '@tanstack/react-query'
import { fetchFedEvents } from '../api/client'

export default function FedCalendarWidget() {
  const query = useQuery({
    queryKey: ['fed-events'],
    queryFn: () => fetchFedEvents(),
    refetchInterval: 600000,
  })

  const events = query.data?.events ?? []
  const now = Date.now()

  const upcoming = events.filter((e) => new Date(e.event_date).getTime() >= now - 7 * 86400000)
  const past = events.filter((e) => new Date(e.event_date).getTime() < now - 7 * 86400000)

  const typeLabels: Record<string, string> = {
    rate_decision: 'FOMC Rate Decision',
    minutes: 'FOMC Minutes',
    speech: 'Fed Speech',
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-3">Fed Calendar</h2>
      {query.isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      {events.length === 0 && !query.isLoading && (
        <p className="text-gray-400 text-sm">No Fed events data yet</p>
      )}
      {events.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide">Upcoming</h3>
          {upcoming.map((e) => {
            const d = new Date(e.event_date)
            const isPast = d.getTime() < now
            return (
              <div
                key={e.id}
                className={`flex items-center justify-between text-sm py-1 border-b border-gray-50 last:border-0 ${
                  isPast ? 'opacity-60' : ''
                }`}
              >
                <div>
                  <span className="font-medium">{typeLabels[e.event_type] || e.event_name}</span>
                </div>
                <div className="text-right">
                  <span className="text-gray-400 text-xs">
                    {d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                  {e.actual_rate !== null && (
                    <span className="text-green-600 font-mono text-xs ml-2">
                      {e.actual_rate.toFixed(2)}%
                    </span>
                  )}
                  {e.expected_rate !== null && e.actual_rate === null && (
                    <span className="text-gray-500 font-mono text-xs ml-2">
                      Est: {e.expected_rate.toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
            )
          })}
          {past.length > 0 && (
            <>
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide pt-2">Recent</h3>
              {past.slice(0, 3).map((e) => {
                const d = new Date(e.event_date)
                return (
                  <div key={e.id} className="flex items-center justify-between text-sm py-1 border-b border-gray-50 last:border-0 opacity-50">
                    <span>{typeLabels[e.event_type] || e.event_name}</span>
                    <div className="text-right">
                      <span className="text-gray-400 text-xs">
                        {d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </span>
                      {e.actual_rate !== null && (
                        <span className="font-mono text-xs ml-2">{e.actual_rate.toFixed(2)}%</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </>
          )}
        </div>
      )}
    </div>
  )
}
