'use client'

import React, { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'

type Json = Record<string, any>

function JsonBlock({ title, data }: { title: string; data: Json | null }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">{title}</h3>
      <pre className="text-xs text-slate-300 overflow-auto max-h-64">
        {data ? JSON.stringify(data, null, 2) : '...'}
      </pre>
    </div>
  )
}

export function DataDiagnostics() {
  const [auditStats, setAuditStats] = useState<Json | null>(null)
  const [driftStats, setDriftStats] = useState<Json | null>(null)
  const [fetchedAt, setFetchedAt] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError('')
      try {
        const [audit, drift] = await Promise.all([
          apiClient.getAuditStats(),
          apiClient.getDriftStats(),
        ])
        setAuditStats(audit)
        setDriftStats(drift)
        setFetchedAt(new Date().toLocaleString())
      } catch (e: any) {
        setError('Failed to fetch diagnostics')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const totalRequests = auditStats?.total_requests ?? 0
  const avgLatency = auditStats?.avg_processing_time_ms ?? 0
  const success = auditStats?.by_status?.success ?? 0
  const successRate = totalRequests > 0 ? (success / totalRequests) * 100 : 0
  const driftAlerts = driftStats?.total_alerts ?? 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200">Diagnostics</h2>
        <div className="text-xs text-slate-400">
          {loading ? 'Fetching…' : fetchedAt ? `Last fetched: ${fetchedAt}` : ''}
          {error && <span className="text-red-400 ml-2">{error}</span>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Summary</div>
          <div className="text-slate-300 text-sm space-y-1">
            <div>Requests: {totalRequests}</div>
            <div>Avg Latency: {avgLatency?.toFixed ? `${avgLatency.toFixed(2)}ms` : avgLatency}</div>
            <div>Success Rate: {successRate.toFixed(2)}%</div>
            <div>Drift Alerts: {driftAlerts}</div>
          </div>
        </div>
        <JsonBlock title="Compliance /api/compliance/statistics" data={auditStats} />
        <JsonBlock title="Drift /api/drift/statistics" data={driftStats} />
      </div>
    </div>
  )
}
