'use client'

import React, { useEffect, useState } from 'react'
import { getComplianceUrl } from '@/lib/config'
import { apiClient } from '@/lib/api'

interface AuditLogEntry {
  timestamp: string
  event: string
  user: string
  status: string
  details: string
}

interface AuditTrailTableProps {
  timeRange?: string
}

export function AuditTrailTable({ timeRange = '24h' }: AuditTrailTableProps) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5

  const getTimeRangeMs = (range: string) => {
    const ranges: Record<string, number> = {
      '1h': 3600000,
      '6h': 21600000,
      '24h': 86400000,
      '7d': 604800000,
      '30d': 2592000000
    }
    return ranges[range] || 86400000
  }

  useEffect(() => {
    // Clear previous data to avoid duplication
    setLogs([])
    setLoading(true)
    setCurrentPage(1)

    // Connect to SSE stream
    const eventSource = new EventSource(getComplianceUrl('stream'))

    eventSource.onmessage = async (event) => {
      try {
        // Fetch recent audit logs with time range
        const endTime = new Date().toISOString()
        const rangeMs = getTimeRangeMs(timeRange)
        const startTime = new Date(Date.now() - rangeMs).toISOString()
        
        const response = await apiClient.queryAuditLogs({
          start_time: startTime,
          end_time: endTime,
          limit: 100
        })

        const mappedLogs: AuditLogEntry[] = (response.results || response.logs || []).map((log: any) => ({
          timestamp: new Date(log.timestamp).toLocaleString('en-US', {
            month: '2-digit',
            day: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
          }),
          event: log.request_id?.includes('INFERENCE') ? 'INFERENCE_COMPLETE' :
                 log.request_id?.includes('DRIFT') ? 'DRIFT_ALERT' :
                 log.request_id?.includes('GDPR') ? 'GDPR_QUERY' :
                 log.request_id?.includes('AUDIT') ? 'AUDIT_EXPORT' :
                 'COMPLIANCE_QUERY',
          user: log.user_id || log.source || 'audit-agent',
          status: log.status === 'success' ? 'SUCCESS' : log.status === 'error' ? 'ERROR' : 'ALERT',
          details: log.model_version
            ? `Model: ${log.model_version.split('/').pop()}, Tokens: ${log.total_tokens || 0}, Latency: ${(log.processing_time_ms || 0).toFixed(1)}ms`
            : `SEC query for document hash: ${log.request_id?.slice(-8) || 'unknown'}`
        }))

        setLogs(mappedLogs)
        setLoading(false)
      } catch (error) {
        console.error('Error fetching audit logs:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error)
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [timeRange])

  const filteredLogs = logs.filter(log =>
    log.event.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.status.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const paginatedLogs = filteredLogs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage)

  return (
    <div className="bg-black border border-neutral-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Audit Trail</h2>
        <div className="flex items-center gap-2">
          <button className="p-2 text-slate-400 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
          </button>
          <button className="p-2 text-slate-400 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Search events..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 pl-10 bg-neutral-900/50 border border-neutral-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-neutral-600"
          />
          <svg className="absolute left-3 top-2.5 w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-400 uppercase">Timestamp</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-400 uppercase">Event</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-400 uppercase">User/Component</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-400 uppercase">Status</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-400 uppercase">Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-slate-400">Loading...</td>
              </tr>
            ) : paginatedLogs.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-slate-400">No logs found</td>
              </tr>
            ) : (
              paginatedLogs.map((log, idx) => (
                <tr key={idx} className="border-b border-neutral-800/50 hover:bg-neutral-900/30 transition-colors">
                  <td className="py-3 px-4 text-xs text-slate-300">{log.timestamp}</td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-medium text-white">{log.event}</span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-300">{log.user}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      log.status === 'SUCCESS' ? 'bg-green-500/20 text-green-400' :
                      log.status === 'ERROR' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400 truncate max-w-xs">{log.details}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-neutral-800">
        <div className="text-xs text-slate-400">
          Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredLogs.length)} of {filteredLogs.length} entries
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="p-2 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + 1
              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-1 text-xs rounded ${
                    currentPage === page
                      ? 'bg-slate-700 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {page}
                </button>
              )
            })}
          </div>
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="p-2 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
