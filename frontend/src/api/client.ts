import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ArticleItem {
  id: string
  headline: string
  body: string
  source_url: string
  published_at: string | null
  source_name: string
  created_at: string
  sentiment: string | null
  confidence: number | null
  impact: string | null
  impact_reason: string | null
  time_horizon: string | null
  summary: string | null
  affected_tickers: string[] | null
  affected_sectors: string[] | null
  scored_by: string | null
  llm_provider: string | null
}

export interface ArticlesResponse {
  articles: ArticleItem[]
  count: number
}

export interface WatchlistItem {
  id: string
  ticker: string
  sector: string | null
  alert_threshold: string
  created_at: string
}

export interface WatchlistResponse {
  watchlist: WatchlistItem[]
}

export interface SentimentTrend {
  hour: string
  bullish_count: number
  bearish_count: number
  neutral_count: number
  avg_confidence: number
}

export interface TickerSentimentResponse {
  ticker: string
  sentiment_trend: SentimentTrend[]
  latest_articles: { id: string; headline: string; source_name: string; published_at: string | null }[]
}

export interface SectorSentiment {
  sector: string
  total: number
  bullish: number
  bearish: number
  neutral: number
  avg_confidence: number
}

export interface SectorSentimentResponse {
  sectors: SectorSentiment[]
}

export interface HealthResponse {
  status: string
  llm_provider: string
  finbert_loaded: boolean
}

export interface HealthLLMResponse {
  ok: boolean
  latency_ms: number
  provider: string
  model: string
  error: string | null
}

export const fetchArticles = async (params: {
  ticker?: string
  sentiment?: string
  impact?: string
  hours?: number
  limit?: number
  offset?: number
}): Promise<ArticlesResponse> => {
  const { data } = await client.get('/articles', { params })
  return data
}

export const fetchArticle = async (id: string): Promise<ArticleItem> => {
  const { data } = await client.get(`/articles/${id}`)
  return data
}

export const fetchWatchlist = async (): Promise<WatchlistResponse> => {
  const { data } = await client.get('/watchlist')
  return data
}

export const addToWatchlist = async (ticker: string, alert_threshold: string = 'medium') => {
  const { data } = await client.post('/watchlist', { ticker, alert_threshold })
  return data
}

export const removeFromWatchlist = async (ticker: string) => {
  const { data } = await client.delete(`/watchlist/${ticker}`)
  return data
}

export const fetchTickerSentiment = async (
  ticker: string,
  hours: number = 168
): Promise<TickerSentimentResponse> => {
  const { data } = await client.get(`/sentiment/ticker/${ticker}`, { params: { hours } })
  return data
}

export const fetchSectorSentiment = async (hours: number = 24): Promise<SectorSentimentResponse> => {
  const { data } = await client.get('/sentiment/sectors', { params: { hours } })
  return data
}

export const fetchHealth = async (): Promise<HealthResponse> => {
  const { data } = await client.get('/health')
  return data
}

export const fetchHealthLLM = async (): Promise<HealthLLMResponse> => {
  const { data } = await client.get('/health/llm')
  return data
}

export const triggerIngestion = async () => {
  const { data } = await client.post('/ingest/trigger')
  return data
}

export default client
