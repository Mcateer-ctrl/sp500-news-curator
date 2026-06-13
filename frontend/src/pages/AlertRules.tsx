import Card from '../components/Card'
import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  fetchAlertRules, createAlertRule, updateAlertRule, deleteAlertRule,
} from "../api/client"

const RULE_TYPES = ["sentiment_shift", "impact_threshold", "earnings", "economic"] as const
const CHANNELS = ["in_app", "email", "push"]

export default function AlertRules() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editingRule, setEditingRule] = useState<number | null>(null)

  const [form, setForm] = useState({ ticker: "", rule_type: "sentiment_shift", threshold: 0.3, channel: "in_app" })

  const query = useQuery({
    queryKey: ["alert-rules"],
    queryFn: fetchAlertRules,
  })

  const rules = query.data?.rules ?? []

  const resetForm = () => {
    setForm({ ticker: "", rule_type: "sentiment_shift", threshold: 0.3, channel: "in_app" })
    setEditingRule(null)
  }

  const openCreate = () => {
    resetForm()
    setShowModal(true)
  }

  const openEdit = (rule: any) => {
    setForm({
      ticker: rule.ticker || "",
      rule_type: rule.rule_type,
      threshold: rule.threshold,
      channel: rule.channel,
    })
    setEditingRule(rule.id)
    setShowModal(true)
  }

  const handleSave = async () => {
    const body = {
      ticker: form.ticker.trim() || null,
      rule_type: form.rule_type,
      threshold: form.threshold,
      channel: form.channel,
    }
    if (editingRule) {
      await updateAlertRule(editingRule, body)
    } else {
      await createAlertRule(body)
    }
    queryClient.invalidateQueries({ queryKey: ["alert-rules"] })
    setShowModal(false)
    resetForm()
  }

  const handleToggle = async (rule: any) => {
    await updateAlertRule(rule.id, { enabled: !rule.enabled })
    queryClient.invalidateQueries({ queryKey: ["alert-rules"] })
  }

  const handleDelete = async (id: number) => {
    await deleteAlertRule(id)
    queryClient.invalidateQueries({ queryKey: ["alert-rules"] })
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Alert Rules</h1>
        <button
          onClick={openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm active:scale-[0.98] transition-transform duration-150"
        >
          New Rule
        </button>
      </div>

      {query.isLoading && <p className="text-gray-400">Loading...</p>}

      {rules.length === 0 && !query.isLoading && (
        <p className="text-gray-400">No alert rules yet. Create one to get started.</p>
      )}

      {rules.length > 0 && (
        <Card padding="default" hover={false}>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Ticker</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Threshold</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Channel</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500"></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs">{r.rule_type}</td>
                  <td className="px-4 py-3 font-mono">{r.ticker || "All"}</td>
                  <td className="px-4 py-3">{r.threshold}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-gray-100 rounded px-2 py-0.5">{r.channel}</span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggle(r)}
                      className={`text-xs px-2 py-0.5 rounded active:scale-[0.98] transition-transform duration-150 ${
                        r.enabled
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {r.enabled ? "Active" : "Paused"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openEdit(r)}
                      className="text-blue-600 hover:text-blue-800 text-xs mr-2 active:scale-[0.98] transition-transform duration-150"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(r.id)}
                      className="text-red-500 hover:text-red-700 text-xs active:scale-[0.98] transition-transform duration-150"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-30">
          <div className="bg-white/40 ring-1 ring-black/[0.06] rounded-[1.25rem] p-[3px] w-full max-w-md">
            <div className="bg-white rounded-[calc(1.25rem-3px)] shadow-inner p-6">
              <h2 className="text-lg font-semibold mb-4">
                {editingRule ? "Edit Rule" : "New Alert Rule"}
              </h2>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Rule Type</label>
                  <select
                    value={form.rule_type}
                    onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
                    className="w-full border rounded px-3 py-1.5 text-sm"
                    disabled={!!editingRule}
                  >
                    {RULE_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Ticker (optional)</label>
                  <input
                    type="text"
                    value={form.ticker}
                    onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })}
                    placeholder="Leave blank for all tickers"
                    className="w-full border rounded px-3 py-1.5 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Threshold</label>
                  <input
                    type="number"
                    step="0.01"
                    value={form.threshold}
                    onChange={(e) => setForm({ ...form, threshold: parseFloat(e.target.value) || 0 })}
                    className="w-full border rounded px-3 py-1.5 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Channel</label>
                  <select
                    value={form.channel}
                    onChange={(e) => setForm({ ...form, channel: e.target.value })}
                    className="w-full border rounded px-3 py-1.5 text-sm"
                  >
                    {CHANNELS.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-5">
                <button
                  onClick={() => { setShowModal(false); resetForm() }}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 active:scale-[0.98] transition-transform duration-150"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm active:scale-[0.98] transition-transform duration-150"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
