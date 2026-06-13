import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchArticles, ArticleItem } from '../api/client'
import Card from './Card'
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
    <div className="space-y-4">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-lg font-semibold text-stone-800">
          News Feed
          {selectedTicker && (
            <span className="text-accent ml-2 font-mono text-base font-medium">{selectedTicker}</span>
          )}
        </h2>
        <span className="text-[0.8125rem] text-stone-400">{articles.length} articles</span>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} padding="compact">
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-stone-100 rounded w-3/4" />
                <div className="h-3 bg-stone-50 rounded w-1/3" />
              </div>
            </Card>
          ))}
        </div>
      )}
      {error && <p className="text-red-500 text-sm">Failed to load articles</p>}

      {articles.map((article: ArticleItem) => (
        <Card key={article.id} padding="default">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <a
                href={article.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[0.9375rem] font-semibold text-stone-900 hover:text-accent leading-snug transition-colors duration-150"
              >
                {article.headline}
              </a>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-[0.75rem] font-medium text-stone-400">
                  {article.source_name}
                </span>
                <span className="text-stone-300">&middot;</span>
                <span className="text-[0.75rem] text-stone-400">
                  {timeAgo(article.published_at)}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <ImpactBadge impact={article.impact} />
            </div>
          </div>

          {article.affected_tickers && article.affected_tickers.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {article.affected_tickers.map((t) => (
                <span
                  key={t}
                  className="bg-accent-light text-accent px-2 py-0.5 rounded-md text-[0.6875rem] font-mono font-medium"
                >
                  {t}
                </span>
              ))}
            </div>
          )}

          {article.sentiment && article.confidence != null && (
            <div className="flex items-center gap-3 mt-3 pt-3 border-t border-stone-100">
              <SentimentPill sentiment={article.sentiment} confidence={article.confidence} />
              {article.summary && (
                <button
                  onClick={() => setExpandedId(expandedId === article.id ? null : article.id)}
                  className="text-[0.75rem] text-accent hover:text-accent-hover font-medium transition-colors duration-150"
                >
                  {expandedId === article.id ? 'Hide' : 'AI Analysis'}
                </button>
              )}
            </div>
          )}

          {expandedId === article.id && article.summary && (
            <div className="mt-3 text-[0.8125rem] text-stone-600 leading-relaxed bg-stone-50 p-3 rounded-lg">
              {article.summary}
              {article.impact_reason && (
                <span className="block mt-2 text-[0.75rem] text-stone-400">
                  {article.impact_reason}
                </span>
              )}
            </div>
          )}
        </Card>
      ))}

      {articles.length >= limit && (
        <button
          onClick={() => setLimit((prev) => prev + 50)}
          className="w-full py-3 text-sm text-stone-500 hover:text-stone-700 font-medium hover:bg-surface-hover rounded-2xl transition-colors duration-200"
        >
          Load more articles
        </button>
      )}
    </div>
  )
}

function SentimentPill({ sentiment, confidence }: { sentiment: string; confidence: number }) {
  const colors: Record<string, string> = {
    bullish: 'bg-emerald-50 text-emerald-700',
    bearish: 'bg-red-50 text-red-700',
    neutral: 'bg-stone-100 text-stone-500',
  }
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[0.6875rem] font-semibold ${colors[sentiment] || colors.neutral}`}>
      {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
      <span className="opacity-60">{Math.round(confidence * 100)}%</span>
    </div>
  )
}
