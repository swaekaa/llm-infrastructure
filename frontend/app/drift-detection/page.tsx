'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { DriftDetectionPanel } from '@/components/dashboard/DriftDetectionPanel'
import { DriftChart } from '@/components/dashboard/DriftChart'
import { getDriftUrl } from '@/lib/config'
import { useState } from 'react'

export default function DriftDetectionPage() {
  const [timeRange, setTimeRange] = useState('24h')
  const [sensitivityLevel, setSensitivityLevel] = useState('0.05')
  const [alertTypeFilter, setAlertTypeFilter] = useState('all')
  const [refreshKey, setRefreshKey] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    alert('Refreshing drift detection data...')
  }

  const exportAlerts = async () => {
    setIsGenerating(true)
    try {
      const response = await fetch(getDriftUrl('alerts') + '?limit=500')
      const data = await response.json()
      
      const csv = [
        ['Timestamp', 'Alert Type', 'Severity', 'Metric', 'Baseline', 'Current', 'Drift Score'].join(','),
        ...(data.alerts || []).map((alert: any) => [
          alert.timestamp,
          alert.alert_type,
          alert.severity,
          alert.metric_name,
          alert.baseline_value,
          alert.current_value,
          alert.drift_score
        ].join(','))
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `drift-alerts-${Date.now()}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const resetBaseline = () => {
    if (confirm('Are you sure you want to reset the baseline? This will recalculate drift detection from current data.')) {
      alert('Baseline reset initiated. This may take a few minutes...')
    }
  }

  const generateReport = async () => {
    setIsGenerating(true)
    alert('Generating comprehensive drift analysis report with visualizations...')
    setTimeout(() => setIsGenerating(false), 2000)
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header with Actions */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Drift Detection</h1>
            <p className="text-slate-400 mt-2">Real-time statistical monitoring and anomaly detection</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
            <button
              onClick={generateReport}
              disabled={isGenerating}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-neutral-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Generate Report
            </button>
          </div>
        </div>

        {/* Advanced Controls */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Time Range */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Time Range</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="1h">Last 1 Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>

            {/* Sensitivity Level */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Sensitivity (p-value)</label>
              <select
                value={sensitivityLevel}
                onChange={(e) => setSensitivityLevel(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="0.01">High (0.01)</option>
                <option value="0.05">Medium (0.05)</option>
                <option value="0.10">Low (0.10)</option>
              </select>
            </div>

            {/* Alert Type Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Alert Type</label>
              <select
                value={alertTypeFilter}
                onChange={(e) => setAlertTypeFilter(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="all">All Types</option>
                <option value="performance">Performance Drift</option>
                <option value="statistical">Statistical Drift</option>
                <option value="latency">Latency Anomaly</option>
                <option value="feedback">User Feedback</option>
              </select>
            </div>

            {/* Export */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Export & Actions</label>
              <button
                onClick={exportAlerts}
                disabled={isGenerating}
                className="w-full px-3 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-neutral-700 text-white text-sm rounded-lg transition-colors"
              >
                Export Alerts (CSV)
              </button>
            </div>
          </div>
        </div>

        {/* Main Drift Detection Panel */}
        <DriftDetectionPanel key={refreshKey} />

        {/* Drift Chart */}
        <DriftChart key={refreshKey} />

        {/* Comprehensive Drift Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Total Alerts
            </h3>
            <div className="text-2xl font-bold text-white">247</div>
            <div className="text-xs text-red-400 mt-1">↑ 18% from baseline</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Critical Alerts
            </h3>
            <div className="text-2xl font-bold text-red-400">23</div>
            <div className="text-xs text-slate-500 mt-1">Requires immediate action</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Warning Alerts
            </h3>
            <div className="text-2xl font-bold text-amber-400">89</div>
            <div className="text-xs text-amber-400 mt-1">Monitor closely</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Info Alerts
            </h3>
            <div className="text-2xl font-bold text-slate-300">135</div>
            <div className="text-xs text-slate-500 mt-1">Informational only</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Drift Score
            </h3>
            <div className="text-2xl font-bold text-amber-400">0.34</div>
            <div className="text-xs text-slate-500 mt-1">Average across metrics</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Detection Rate
            </h3>
            <div className="text-2xl font-bold text-green-400">98.2%</div>
            <div className="text-xs text-green-400 mt-1">↑ High accuracy</div>
          </div>
        </div>

        {/* Advanced Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Baseline Statistics */}
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
              Baseline Statistics
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Samples in baseline:</span>
                <span className="text-lg font-semibold text-white">1,250</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Recent samples:</span>
                <span className="text-lg font-semibold text-white">847</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Baseline date:</span>
                <span className="text-sm font-medium text-white">2026-01-01</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Drift sensitivity:</span>
                <span className="text-lg font-semibold text-amber-400">{sensitivityLevel}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Confidence level:</span>
                <span className="text-lg font-semibold text-green-400">95%</span>
              </div>
            </div>
          </div>

          {/* Detection Methods */}
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
              Detection Methods
            </h2>
            <div className="space-y-3">
              <div className="bg-neutral-800/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">Kolmogorov-Smirnov</span>
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                </div>
                <p className="text-xs text-slate-400">Distribution comparison test</p>
                <div className="text-xs text-green-400 mt-1">Active • 156 detections</div>
              </div>
              <div className="bg-neutral-800/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">Chi-Square Test</span>
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                </div>
                <p className="text-xs text-slate-400">Categorical data analysis</p>
                <div className="text-xs text-green-400 mt-1">Active • 68 detections</div>
              </div>
              <div className="bg-neutral-800/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">PSI (Population Stability Index)</span>
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                </div>
                <p className="text-xs text-slate-400">Population shift detection</p>
                <div className="text-xs text-green-400 mt-1">Active • 23 detections</div>
              </div>
            </div>
          </div>

          {/* Alert Actions */}
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
              Alert Actions
            </h2>
            <div className="space-y-3">
              <button
                onClick={resetBaseline}
                className="w-full px-4 py-3 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reset Baseline
              </button>
              <button
                onClick={exportAlerts}
                disabled={isGenerating}
                className="w-full px-4 py-3 text-sm font-medium text-white bg-neutral-700 hover:bg-neutral-600 disabled:bg-neutral-800 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Alerts
              </button>
              <button
                className="w-full px-4 py-3 text-sm font-medium text-white bg-neutral-700 hover:bg-neutral-600 rounded-lg transition-colors flex items-center justify-center gap-2"
                onClick={() => alert('Configuring notification settings...')}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                Configure Alerts
              </button>
            </div>
          </div>
        </div>

        {/* Metric-Specific Analysis */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Metric-Specific Drift Analysis</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { metric: 'Response Latency', baseline: '28.3ms', current: '45.7ms', drift: 0.61, status: 'critical' },
              { metric: 'Token Count', baseline: '156', current: '189', drift: 0.21, status: 'warning' },
              { metric: 'Error Rate', baseline: '2.1%', current: '4.3%', drift: 0.52, status: 'critical' },
              { metric: 'Model Confidence', baseline: '0.89', current: '0.82', drift: 0.31, status: 'warning' },
              { metric: 'User Satisfaction', baseline: '4.2/5', current: '3.8/5', drift: 0.28, status: 'warning' },
              { metric: 'Cache Hit Rate', baseline: '67%', current: '71%', drift: 0.12, status: 'normal' }
            ].map((item) => (
              <div key={item.metric} className="bg-neutral-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-white">{item.metric}</h3>
                  <span className={`w-2 h-2 rounded-full ${
                    item.status === 'critical' ? 'bg-red-500' :
                    item.status === 'warning' ? 'bg-amber-500' : 'bg-green-500'
                  }`}></span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400">Baseline:</span>
                    <div className="text-white font-medium">{item.baseline}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Current:</span>
                    <div className="text-white font-medium">{item.current}</div>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Drift Score</span>
                    <span className={`font-medium ${
                      item.drift > 0.5 ? 'text-red-400' :
                      item.drift > 0.3 ? 'text-amber-400' : 'text-green-400'
                    }`}>{item.drift.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-neutral-700 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        item.drift > 0.5 ? 'bg-red-500' :
                        item.drift > 0.3 ? 'bg-amber-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(item.drift * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
