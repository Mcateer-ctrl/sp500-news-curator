import Card from '../components/Card'
import { useQuery } from '@tanstack/react-query'
import { fetchHealth, fetchHealthLLM, triggerIngestion } from '../api/client'
import { useState } from 'react'

export default function Settings() {
  const [ingestResult, setIngestResult] = useState<string | null>(null)

  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30000,
  })

  const llmQuery = useQuery({
    queryKey: ['health-llm'],
    queryFn: fetchHealthLLM,
    enabled: false,
  })

  const handleTestLLM = () => {
    llmQuery.refetch()
  }

  const handleIngest = async () => {
    try {
      setIngestResult('Ingesting...')
      const result = await triggerIngestion()
      setIngestResult(`Done: ${result.new} new articles, ${result.fetched} fetched total`)
    } catch {
      setIngestResult('Ingestion failed')
    }
  }

  const health = healthQuery.data

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* System Status */}
      <Card padding="spacious" hover={false}>
        <h2 className="text-lg font-semibold mb-4">System Status</h2>
        {healthQuery.isLoading && <p className="text-gray-400">Loading...</p>}
        {health && (
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <dt className="text-gray-500">Status</dt>
            <dd className="font-medium text-green-600">{health.status}</dd>

            <dt className="text-gray-500">LLM Provider</dt>
            <dd className="font-mono">{health.llm_provider}</dd>

            <dt className="text-gray-500">FinBERT Loaded</dt>
            <dd>{health.finbert_loaded ? '\u2705 Yes' : '\u23f3 Not yet'}</dd>
          </dl>
        )}
      </Card>

      {/* LLM Test */}
      <Card padding="spacious" hover={false}>
        <h2 className="text-lg font-semibold mb-4">LLM Connection Test</h2>
        <button
          onClick={handleTestLLM}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm"
          disabled={llmQuery.isFetching}
        >
          {llmQuery.isFetching ? 'Testing...' : 'Test LLM Connection'}
        </button>
        {llmQuery.data && (
          <dl className="grid grid-cols-2 gap-4 text-sm mt-4">
            <dt className="text-gray-500">OK</dt>
            <dd className={llmQuery.data.ok ? 'text-green-600' : 'text-red-600'}>
              {llmQuery.data.ok ? '\u2705 Yes' : '\u274c No'}
            </dd>

            <dt className="text-gray-500">Provider</dt>
            <dd className="font-mono">{llmQuery.data.provider}</dd>

            <dt className="text-gray-500">Model</dt>
            <dd className="font-mono">{llmQuery.data.model}</dd>

            <dt className="text-gray-500">Latency</dt>
            <dd>{llmQuery.data.latency_ms}ms</dd>

            {llmQuery.data.error && (
              <>
                <dt className="text-gray-500">Error</dt>
                <dd className="text-red-600 text-xs">{llmQuery.data.error}</dd>
              </>
            )}
          </dl>
        )}
      </Card>

      {/* Manual Ingestion */}
      <Card padding="spacious" hover={false}>
        <h2 className="text-lg font-semibold mb-4">Manual Ingestion</h2>
        <button
          onClick={handleIngest}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm"
        >
          Trigger Ingestion
        </button>
        {ingestResult && (
          <p className="text-sm text-gray-600 mt-2">{ingestResult}</p>
        )}
      </Card>

      {/* Email Configuration */}
      <Card padding="spacious" hover={false}>
        <h2 className="text-lg font-semibold mb-4">Alert Email Configuration</h2>
        <p className="text-sm text-gray-500 mb-4">
          Configure SMTP settings in your .env file to enable email alerts via Gmail.
          Requires a Gmail App Password (2FA must be enabled).
        </p>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <dt className="text-gray-500">SMTP Host</dt>
          <dd className="font-mono">smtp.gmail.com:587</dd>

          <dt className="text-gray-500">Status</dt>
          <dd>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-yellow-400" />
              <span>Check .env to enable</span>
            </span>
          </dd>
        </dl>
      </Card>
    </div>
  )
}