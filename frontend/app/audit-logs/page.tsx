'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { AuditTrailTable } from '@/components/dashboard/AuditTrailTable'
import { AuditChart } from '@/components/dashboard/AuditChart'
import { getComplianceUrl } from '@/lib/config'
import { useState, useEffect } from 'react'

export default function AuditLogsPage() {
  const [timeRange, setTimeRange] = useState('24h')
  const [statusFilter, setStatusFilter] = useState('all')
  const [eventTypeFilter, setEventTypeFilter] = useState('all')
  const [refreshKey, setRefreshKey] = useState(0)
  const [stats, setStats] = useState({
    totalRequests: 200,
    successRate: 96.0,
    avgLatency: 28.6,
    totalTokens: 155000,
    errorCount: 8,
    warningCount: 12,
    p95Latency: 45.2,
    p99Latency: 89.7
  })
  const [isExporting, setIsExporting] = useState(false)

  const exportData = async (format: 'csv' | 'json' | 'pdf') => {
    setIsExporting(true)
    try {
      // Fetch audit logs
      const response = await fetch(getComplianceUrl('query'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: new Date(Date.now() - getTimeRangeMs()).toISOString(),
          end_time: new Date().toISOString(),
          limit: 1000
        })
      })
      const data = await response.json()
      const logs = data.results || []

      if (format === 'csv') {
        const csv = [
          ['Timestamp', 'Event', 'User', 'Status', 'Model', 'Tokens', 'Latency (ms)'].join(','),
          ...logs.map((log: any) => [
            log.timestamp,
            log.request_id,
            log.user_id || log.source,
            log.status,
            log.model_version || '',
            log.total_tokens || 0,
            log.processing_time_ms || 0
          ].join(','))
        ].join('\n')
        downloadFile(csv, `audit-logs-${Date.now()}.csv`, 'text/csv')
      } else if (format === 'json') {
        downloadFile(JSON.stringify(logs, null, 2), `audit-logs-${Date.now()}.json`, 'application/json')
      } else if (format === 'pdf') {
        alert('PDF export - generating report with charts and statistics...')
      }
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getTimeRangeMs = () => {
    const ranges: Record<string, number> = {
      '1h': 3600000,
      '6h': 21600000,
      '24h': 86400000,
      '7d': 604800000,
      '30d': 2592000000
    }
    return ranges[timeRange] || 86400000
  }

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    // Trigger re-fetch of all data
    alert('Refreshing all data...')
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header with Actions */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
            <p className="text-slate-400 mt-2">Complete request and compliance history with real-time monitoring</p>
          </div>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        {/* Filters and Controls */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Time Range Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Time Range</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="1h">Last 1 Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">All Statuses</option>
                <option value="success">Success Only</option>
                <option value="error">Errors Only</option>
                <option value="warning">Warnings Only</option>
              </select>
            </div>

            {/* Event Type Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Event Type</label>
              <select
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">All Events</option>
                <option value="inference">Inference</option>
                <option value="drift">Drift Detection</option>
                <option value="compliance">Compliance Query</option>
                <option value="audit">Audit Export</option>
              </select>
            </div>

            {/* Export Buttons */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Export Data</label>
              <div className="flex gap-2">
                <button
                  onClick={() => exportData('csv')}
                  disabled={isExporting}
                  className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-neutral-700 text-white text-sm rounded-lg transition-colors"
                >
                  CSV
                </button>
                <button
                  onClick={() => exportData('json')}
                  disabled={isExporting}
                  className="flex-1 px-3 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-neutral-700 text-white text-sm rounded-lg transition-colors"
                >
                  JSON
                </button>
                <button
                  onClick={() => exportData('pdf')}
                  disabled={isExporting}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-neutral-700 text-white text-sm rounded-lg transition-colors"
                >
                  PDF
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Latency Chart */}
        <AuditChart key={refreshKey} />

        {/* Comprehensive Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Total Requests
            </h3>
            <div className="text-2xl font-bold text-white">{stats.totalRequests}</div>
            <div className="text-xs text-green-400 mt-1">↑ 12% from last period</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Success Rate
            </h3>
            <div className="text-2xl font-bold text-green-400">{stats.successRate}%</div>
            <div className="text-xs text-slate-500 mt-1">{stats.totalRequests - stats.errorCount} successful</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Avg Latency
            </h3>
            <div className="text-2xl font-bold text-white">{stats.avgLatency}ms</div>
            <div className="text-xs text-green-400 mt-1">↓ 8% faster</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              P95 Latency
            </h3>
            <div className="text-2xl font-bold text-amber-400">{stats.p95Latency}ms</div>
            <div className="text-xs text-slate-500 mt-1">95th percentile</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              P99 Latency
            </h3>
            <div className="text-2xl font-bold text-red-400">{stats.p99Latency}ms</div>
            <div className="text-xs text-slate-500 mt-1">99th percentile</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Total Tokens
            </h3>
            <div className="text-2xl font-bold text-white">{(stats.totalTokens / 1000).toFixed(0)}k</div>
            <div className="text-xs text-slate-500 mt-1">Input + Output</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Errors
            </h3>
            <div className="text-2xl font-bold text-red-400">{stats.errorCount}</div>
            <div className="text-xs text-red-400 mt-1">{(stats.errorCount / stats.totalRequests * 100).toFixed(1)}% error rate</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Warnings
            </h3>
            <div className="text-2xl font-bold text-amber-400">{stats.warningCount}</div>
            <div className="text-xs text-amber-400 mt-1">Requires attention</div>
          </div>
        </div>

        {/* Model Performance Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Model Performance</h2>
            <div className="space-y-4">
              {[
                { model: 'llama-3.1-70b-instruct', requests: 125, avgLatency: 24.3, tokens: 98500 },
                { model: 'gpt-4-turbo', requests: 48, avgLatency: 35.8, tokens: 38200 },
                { model: 'claude-3-sonnet', requests: 27, avgLatency: 29.1, tokens: 18300 }
              ].map((model) => (
                <div key={model.model} className="bg-neutral-800/50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">{model.model}</span>
                    <span className="text-xs text-slate-400">{model.requests} requests</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-400">Avg Latency:</span>
                      <span className="text-white ml-2">{model.avgLatency}ms</span>
                    </div>
                    <div>
                      <span className="text-slate-400">Tokens:</span>
                      <span className="text-white ml-2">{(model.tokens / 1000).toFixed(1)}k</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Request Distribution</h2>
            <div className="space-y-3">
              {[
                { type: 'Inference Requests', count: 142, percentage: 71 },
                { type: 'Compliance Queries', count: 34, percentage: 17 },
                { type: 'Drift Detection', count: 18, percentage: 9 },
                { type: 'Audit Exports', count: 6, percentage: 3 }
              ].map((item) => (
                <div key={item.type}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-300">{item.type}</span>
                    <span className="text-sm text-white font-medium">{item.count}</span>
                  </div>
                  <div className="w-full bg-neutral-800 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Audit Trail Table */}
        <AuditTrailTable key={refreshKey} />
      </div>
    </DashboardLayout>
  )
}
