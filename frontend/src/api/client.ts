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

export interface SentimentHistoryItem {
  date: string
  composite_score: number
  bullish_count: number
  bearish_count: number
  neutral_count: number
  total_articles: number
  avg_confidence: number
}

export interface SentimentHistoryResponse {
  ticker: string
  history: SentimentHistoryItem[]
}

export interface EarningsItem {
  id: number
  ticker: string
  fiscal_quarter: string | null
  eps_estimate: number | null
  eps_actual: number | null
  revenue_estimate: number | null
  revenue_actual: number | null
  report_date: string
  report_time: string | null
}

export interface EarningsResponse {
  earnings: EarningsItem[]
}

export interface IndicatorValue {
  date: string
  value: number
  previous_value: number | null
  source: string
}

export interface IndicatorsResponse {
  indicators: Record<string, IndicatorValue[]>
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

export interface FedEventItem {
  id: number
  event_name: string
  event_date: string
  event_type: string
  actual_rate: number | null
  expected_rate: number | null
}

export interface FedEventsResponse {
  events: FedEventItem[]
}

export interface ThirteenFFilingItem {
  id: number
  filer_name: string
  ticker: string
  shares: number
  value: number | null
  filing_date: string
  period: string | null
}

export interface ThirteenFFilingsResponse {
  filings: ThirteenFFilingItem[]
}

export interface AlertRuleItem {
  id: number
  ticker: string | null
  rule_type: string
  threshold: number
  channel: string
  enabled: boolean
  last_triggered_at: string | null
  created_at: string
}

export interface AlertRulesResponse {
  rules: AlertRuleItem[]
}

export interface NotificationItem {
  id: number
  title: string
  body: string
  ticker: string | null
  notification_type: string
  channel: string
  status: string
  read_at: string | null
  created_at: string
}

export interface NotificationsResponse {
  notifications: NotificationItem[]
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

export const fetchSentimentHistory = async (
  ticker: string,
  days: number = 30
): Promise<SentimentHistoryResponse> => {
  const { data } = await client.get(`/sentiment/history/${ticker}`, { params: { days } })
  return data
}

export const fetchEarnings = async (params: {
  ticker?: string
  upcoming?: boolean
  days?: number
}): Promise<EarningsResponse> => {
  const { data } = await client.get('/earnings', { params })
  return data
}

export const fetchIndicators = async (
  names: string = 'cpi,nonfarm_payrolls,unemployment_rate',
  days: number = 90
): Promise<IndicatorsResponse> => {
  const { data } = await client.get('/indicators', { params: { names, days } })
  return data
}


export const fetchAlertRules = async (): Promise<AlertRulesResponse> => {
  const { data } = await client.get("/alerts/rules")
  return data
}

export const createAlertRule = async (body: {
  ticker?: string | null
  rule_type: string
  threshold: number
  channel?: string
}) => {
  const { data } = await client.post("/alerts/rules", body)
  return data
}

export const updateAlertRule = async (id: number, body: {
  ticker?: string | null
  threshold?: number
  channel?: string
  enabled?: boolean
}) => {
  const { data } = await client.put(`/alerts/rules/${id}`, body)
  return data
}

export const deleteAlertRule = async (id: number) => {
  const { data } = await client.delete(`/alerts/rules/${id}`)
  return data
}

export const fetchNotifications = async (unread: boolean = true): Promise<NotificationsResponse> => {
  const { data } = await client.get("/alerts/notifications", { params: { unread: unread ? "true" : "false" } })
  return data
}

export const markNotificationRead = async (id: number) => {
  const { data } = await client.put(`/alerts/notifications/${id}/read`)
  return data
}

export const markAllNotificationsRead = async () => {
  const { data } = await client.post("/alerts/notifications/read-all")
  return data
}

export const subscribePush = async (subscription: {
  endpoint: string
  p256dh_key: string
  auth_key: string
}) => {
  const { data } = await client.post("/alerts/push/subscribe", subscription)
  return data
}

export const unsubscribePush = async (subscription: {
  endpoint: string
  p256dh_key: string
  auth_key: string
}) => {
  const { data } = await client.delete("/alerts/push/subscribe", { data: subscription })
  return data
}

export interface ThirteenFFilingItem {
  id: number
  ticker: string
  cik: string | null
  filing_date: string
  period_date: string
  shares_held: number | null
  value: number | null
}

export interface ThirteenFFilingsResponse {
  filings: ThirteenFFilingItem[]
}

export interface FedEventItem {
  id: number
  event_name: string
  event_date: string
  event_type: string
  actual_rate: number | null
  expected_rate: number | null
}

export interface FedEventsResponse {
  events: FedEventItem[]
}

export const fetchThirteenFFilings = async (params?: {
  ticker?: string
  days?: number
}): Promise<ThirteenFFilingsResponse> => {
  const { data } = await client.get('/13f/filings', { params })
  return data
}

export const fetchFedEvents = async (params?: {
  event_type?: string
}): Promise<FedEventsResponse> => {
  const { data } = await client.get('/fed/events', { params })
  return data
}

export default client
