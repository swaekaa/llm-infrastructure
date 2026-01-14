'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { OverviewCards } from '@/components/dashboard/OverviewCards'
import { AuditChart } from '@/components/dashboard/AuditChart'
import { DriftChart } from '@/components/dashboard/DriftChart'
import { DriftDetectionPanel } from '@/components/dashboard/DriftDetectionPanel'
import { SystemHealthPanel } from '@/components/dashboard/SystemHealthPanel'
import { AuditTrailTable } from '@/components/dashboard/AuditTrailTable'
import { useState } from 'react'

export default function DashboardPage() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState('5')
  const [dateRange, setDateRange] = useState('24h')
  const [refreshKey, setRefreshKey] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleManualRefresh = () => {
    setIsRefreshing(true)
    // Force re-render by updating key with unique value
    setRefreshKey(prev => prev + 1)
    // Reset after 1 second
    setTimeout(() => {
      setIsRefreshing(false)
    }, 1000)
  }

  const handleTimeRangeChange = (newRange: string) => {
    setDateRange(newRange)
    // Force re-fetch with new time range
    setRefreshKey(prev => prev + 1)
  }

  const exportDashboard = () => {
    try {
      // Create a simple text export
      const data = `Dashboard Export - ${new Date().toISOString()}\nTime Range: ${dateRange}\n\nStats:\n- Uptime: 99.8%\n- Throughput: 3.2k/hr\n- Cache Hit: 67.3%\n- Queue Size: 12\n- Cost (24h): $47.20\n- Active Users: 28`
      const blob = new Blob([data], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dashboard-${Date.now()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      alert('✓ Dashboard exported successfully!')
    } catch (error) {
      alert('Export failed: ' + (error as Error).message)
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Dashboard Controls */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              {/* Date Range Selector */}
              <div className="flex items-center gap-2">
                <label className="text-sm text-slate-400">Time Range:</label>
                <select
                  value={dateRange}
                  onChange={(e) => handleTimeRangeChange(e.target.value)}
                  className="px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="1h">Last Hour</option>
                  <option value="6h">Last 6 Hours</option>
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                </select>
              </div>

              {/* Auto Refresh Toggle */}
              <div className="flex items-center gap-2">
                <label className="text-sm text-slate-400">Auto-Refresh:</label>
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    autoRefresh ? 'bg-green-600' : 'bg-neutral-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      autoRefresh ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Refresh Interval */}
              {autoRefresh && (
                <div className="flex items-center gap-2">
                  <label className="text-sm text-slate-400">Interval:</label>
                  <select
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(e.target.value)}
                    className="px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value="2">2s</option>
                    <option value="5">5s</option>
                    <option value="10">10s</option>
                    <option value="30">30s</option>
                    <option value="60">1m</option>
                  </select>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleManualRefresh}
                disabled={isRefreshing}
                className="px-4 py-1.5 bg-neutral-800 hover:bg-neutral-700 disabled:bg-neutral-800 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
              >
                <svg className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {isRefreshing ? 'Refreshing...' : 'Refresh Now'}
              </button>
              <button
                onClick={exportDashboard}
                className="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Overview Cards */}
        <OverviewCards key={refreshKey} timeRange={dateRange} />

        {/* Main Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AuditChart key={`audit-${refreshKey}`} timeRange={dateRange} />
          <DriftChart key={`drift-${refreshKey}`} timeRange={dateRange} />
        </div>

        {/* Drift Detection and System Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DriftDetectionPanel key={`drift-panel-${refreshKey}`} timeRange={dateRange} />
          <SystemHealthPanel key={`health-${refreshKey}`} timeRange={dateRange} />
        </div>

        {/* Quick Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Uptime</div>
            <div className="text-xl font-bold text-green-400">99.8%</div>
            <div className="text-xs text-slate-500 mt-1">45 days</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Throughput</div>
            <div className="text-xl font-bold text-white">3.2k/hr</div>
            <div className="text-xs text-green-400 mt-1">↑ 15%</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Cache Hit</div>
            <div className="text-xl font-bold text-white">67.3%</div>
            <div className="text-xs text-slate-500 mt-1">Optimal</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Queue Size</div>
            <div className="text-xl font-bold text-white">12</div>
            <div className="text-xs text-slate-500 mt-1">Messages</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Cost (24h)</div>
            <div className="text-xl font-bold text-white">$47.20</div>
            <div className="text-xs text-amber-400 mt-1">↑ $3.20</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Active Users</div>
            <div className="text-xl font-bold text-white">28</div>
            <div className="text-xs text-green-400 mt-1">Online now</div>
          </div>
        </div>

        {/* Audit Trail Table */}
        <AuditTrailTable key={`table-${refreshKey}`} timeRange={dateRange} />
      </div>
    </DashboardLayout>
  )
}
