'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { getComplianceUrl } from '@/lib/config'
import { useState } from 'react'

export default function CompliancePage() {
  const [selectedStandard, setSelectedStandard] = useState<string | null>(null)
  const [reportType, setReportType] = useState('full')
  const [timeRange, setTimeRange] = useState('30d')
  const [isGenerating, setIsGenerating] = useState(false)

  const standards = [
    { 
      name: 'SEC', 
      fullName: 'Securities and Exchange Commission',
      status: 'Compliant', 
      color: 'green',
      lastAudit: '2026-01-10',
      requirements: 42,
      met: 42,
      inProgress: 0
    },
    { 
      name: 'FINRA', 
      fullName: 'Financial Industry Regulatory Authority',
      status: 'Compliant', 
      color: 'green',
      lastAudit: '2026-01-08',
      requirements: 38,
      met: 38,
      inProgress: 0
    },
    { 
      name: 'GDPR', 
      fullName: 'General Data Protection Regulation',
      status: 'Compliant', 
      color: 'green',
      lastAudit: '2026-01-12',
      requirements: 56,
      met: 54,
      inProgress: 2
    },
    { 
      name: 'CCPA', 
      fullName: 'California Consumer Privacy Act',
      status: 'Compliant', 
      color: 'green',
      lastAudit: '2026-01-11',
      requirements: 31,
      met: 31,
      inProgress: 0
    },
  ]

  const exportAuditTrail = async (format: 'csv' | 'json' | 'pdf') => {
    setIsGenerating(true)
    try {
      const response = await fetch(getComplianceUrl('query'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          end_time: new Date().toISOString(),
          limit: 1000
        })
      })
      const data = await response.json()
      const logs = data.results || []

      if (format === 'csv') {
        const csv = [
          ['Timestamp', 'Event', 'User', 'Status', 'Details'].join(','),
          ...logs.map((log: any) => [
            log.timestamp,
            log.request_id,
            log.user_id || log.source,
            log.status,
            `"${log.model_version || 'N/A'}"`
          ].join(','))
        ].join('\n')
        downloadFile(csv, `audit-trail-${format}-${Date.now()}.csv`, 'text/csv')
      } else if (format === 'json') {
        downloadFile(JSON.stringify(logs, null, 2), `audit-trail-${Date.now()}.json`, 'application/json')
      } else if (format === 'pdf') {
        alert('PDF report generation started. This includes all audit trails, compliance status, and statistics.')
      }
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsGenerating(false)
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

  const generateComplianceReport = () => {
    setIsGenerating(true)
    alert(`Generating ${reportType} compliance report for ${timeRange} time period with all regulatory standards...`)
    setTimeout(() => setIsGenerating(false), 2000)
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Compliance Dashboard</h1>
            <p className="text-slate-400 mt-2">Regulatory compliance monitoring and audit reporting</p>
          </div>
          <button
            onClick={() => alert('Refreshing compliance status...')}
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Status
          </button>
        </div>

        {/* Overall Compliance Score */}
        <div className="bg-gradient-to-r from-green-900/20 to-green-800/20 border border-green-800 rounded-lg p-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-green-400 uppercase tracking-wider mb-2">
                Overall Compliance Score
              </h2>
              <div className="text-5xl font-bold text-white mb-2">99.2%</div>
              <p className="text-slate-300">4 of 4 standards compliant • 165 of 167 requirements met</p>
            </div>
            <div className="text-center">
              <div className="w-32 h-32 rounded-full border-8 border-green-500 flex items-center justify-center">
                <svg className="w-16 h-16 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="text-xs text-slate-400 mt-2">Last audit: Today</p>
            </div>
          </div>
        </div>

        {/* Regulatory Standards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {standards.map((standard) => (
            <div
              key={standard.name}
              className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 hover:border-green-600 transition-colors cursor-pointer"
              onClick={() => setSelectedStandard(selectedStandard === standard.name ? null : standard.name)}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">{standard.name}</h3>
                  <p className="text-sm text-slate-400 mt-1">{standard.fullName}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full bg-${standard.color}-500`} />
                  <span className="text-green-400 text-sm font-medium">✓ {standard.status}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">Requirements</div>
                  <div className="text-xl font-bold text-white">{standard.requirements}</div>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">Met</div>
                  <div className="text-xl font-bold text-green-400">{standard.met}</div>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">In Progress</div>
                  <div className="text-xl font-bold text-amber-400">{standard.inProgress}</div>
                </div>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Last Audit: {standard.lastAudit}</span>
                <span className="text-green-400">{((standard.met / standard.requirements) * 100).toFixed(1)}% Complete</span>
              </div>

              {/* Expanded Details */}
              {selectedStandard === standard.name && (
                <div className="mt-4 pt-4 border-t border-neutral-800">
                  <h4 className="text-sm font-medium text-white mb-3">Recent Compliance Checks</h4>
                  <div className="space-y-2">
                    {[
                      { check: 'Data Encryption at Rest', status: 'pass', date: '2026-01-14' },
                      { check: 'Access Control Audit', status: 'pass', date: '2026-01-13' },
                      { check: 'Retention Policy Review', status: 'pass', date: '2026-01-12' },
                      { check: 'Privacy Impact Assessment', status: 'in-progress', date: '2026-01-14' }
                    ].map((check, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs bg-neutral-800/30 rounded p-2">
                        <span className="text-slate-300">{check.check}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400">{check.date}</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            check.status === 'pass' ? 'bg-green-900/50 text-green-400' :
                            'bg-amber-900/50 text-amber-400'
                          }`}>
                            {check.status === 'pass' ? '✓ Pass' : '⋯ In Progress'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Report Generation Section */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Generate Compliance Report</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Report Type</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="full">Full Compliance Report</option>
                <option value="summary">Executive Summary</option>
                <option value="technical">Technical Audit Report</option>
                <option value="regulatory">Regulatory Submission</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Time Period</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="1y">Last Year</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Include Standards</label>
              <select
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">All Standards</option>
                <option value="sec">SEC Only</option>
                <option value="finra">FINRA Only</option>
                <option value="gdpr">GDPR Only</option>
                <option value="ccpa">CCPA Only</option>
              </select>
            </div>
          </div>

          <button
            onClick={generateComplianceReport}
            disabled={isGenerating}
            className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-neutral-700 rounded-lg text-white font-medium transition flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {isGenerating ? 'Generating Report...' : 'Generate Compliance Report'}
          </button>
        </div>

        {/* Export Options */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Export Audit Trail</h2>
          <p className="text-sm text-slate-400 mb-4">Download complete audit history for regulatory compliance and archival purposes</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button
              onClick={() => exportAuditTrail('csv')}
              disabled={isGenerating}
              className="px-4 py-3 bg-amber-600 hover:bg-amber-700 disabled:bg-neutral-700 rounded-lg text-white font-medium transition flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export CSV
            </button>
            <button
              onClick={() => exportAuditTrail('json')}
              disabled={isGenerating}
              className="px-4 py-3 bg-neutral-700 hover:bg-neutral-600 disabled:bg-neutral-800 rounded-lg text-white font-medium transition flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export JSON
            </button>
            <button
              onClick={() => exportAuditTrail('pdf')}
              disabled={isGenerating}
              className="px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-neutral-700 rounded-lg text-white font-medium transition flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              Generate PDF Report
            </button>
          </div>
        </div>

        {/* Compliance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Audit Events (30d)
            </h3>
            <div className="text-2xl font-bold text-white">1,847</div>
            <div className="text-xs text-green-400 mt-1">↑ 23% from last month</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Compliance Violations
            </h3>
            <div className="text-2xl font-bold text-green-400">0</div>
            <div className="text-xs text-slate-500 mt-1">No violations detected</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Policy Updates
            </h3>
            <div className="text-2xl font-bold text-white">3</div>
            <div className="text-xs text-amber-400 mt-1">Pending review</div>
          </div>
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Next Audit
            </h3>
            <div className="text-2xl font-bold text-white">21d</div>
            <div className="text-xs text-slate-500 mt-1">Feb 4, 2026</div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
