import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchArticles, ArticleItem } from '../api/client'
import ImpactBadge from './ImpactBadge'

interface NewsFeedProps {
  selectedTicker: string | null
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diffMs = now - then
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}

function sentimentIcon(sentiment: string | null): string {
  if (sentiment === 'bullish') return '🟢'
  if (sentiment === 'bearish') return '🔴'
  return '⚪'
}

export default function NewsFeed({ selectedTicker }: NewsFeedProps) {
  const [limit, setLimit] = useState(50)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['articles', selectedTicker, limit],
    queryFn: () =>
      fetchArticles({
        ticker: selectedTicker ?? undefined,
        hours: 168,
        limit,
      }),
    refetchInterval: 60000,
  })

  const articles = data?.articles ?? []

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          News Feed
          {selectedTicker && (
            <span className="text-blue-600 ml-2 font-mono">{selectedTicker}</span>
          )}
        </h2>
        <span className="text-sm text-gray-400">{articles.length} articles</span>
      </div>

      {isLoading && <p className="text-gray-400 text-sm">Loading articles...</p>}
      {error && <p className="text-red-500 text-sm">Failed to load articles</p>}

      {articles.map((article: ArticleItem) => (
        <div key={article.id} className="bg-white rounded-lg shadow p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <a
                href={article.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-semibold text-gray-900 hover:text-blue-600 leading-tight"
              >
                {article.headline}
              </a>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                <span>{article.source_name}</span>
                <span>{timeAgo(article.published_at)}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <ImpactBadge impact={article.impact} />
              <span className="text-sm" title={article.sentiment ?? ''}>
                {sentimentIcon(article.sentiment)}
              </span>
              {article.confidence != null && (
                <span className="text-xs text-gray-400">
                  {Math.round(article.confidence * 100)}%
                </span>
              )}
            </div>
          </div>

          {article.affected_tickers && article.affected_tickers.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {article.affected_tickers.map((t) => (
                <span
                  key={t}
                  className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs font-mono"
                >
                  {t}
                </span>
              ))}
            </div>
          )}

          {article.summary && (
            <div className="mt-2">
              <button
                onClick={() => setExpandedId(expandedId === article.id ? null : article.id)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {expandedId === article.id ? 'Hide summary' : 'Show AI summary'}
              </button>
              {expandedId === article.id && (
                <p className="text-sm text-gray-600 mt-1 bg-blue-50 p-2 rounded">
                  {article.summary}
                  {article.impact_reason && (
                    <span className="block text-xs text-gray-500 mt-1">
                      Impact: {article.impact_reason}
                    </span>
                  )}
                </p>
              )}
            </div>
          )}
        </div>
      ))}

      {articles.length >= limit && (
        <button
          onClick={() => setLimit((prev) => prev + 50)}
          className="w-full py-2 text-sm text-blue-600 hover:text-blue-800 bg-white rounded-lg shadow"
        >
          Load more
        </button>
      )}
    </div>
  )
}
