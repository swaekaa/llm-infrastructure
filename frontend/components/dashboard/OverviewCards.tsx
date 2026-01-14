'use client'

import React, { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'
import { config } from '@/lib/config'

interface OverviewCardsProps {
  timeRange?: string
}

interface MetricCardProps {
  title: string
  value: string
  subtitle?: string
  trend?: {
    value: string
    positive: boolean
  }
  loading?: boolean
}

function MetricCard({ title, value, subtitle, trend, loading }: MetricCardProps) {
  return (
    <div className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-6">
      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
        {title}
      </h3>
      <div className="text-3xl font-bold text-white mb-2">
        {loading ? '...' : value}
      </div>
      {subtitle && (
        <p className="text-sm text-slate-500">{subtitle}</p>
      )}
      {trend && !loading && (
        <p className={`text-sm mt-2 ${trend.positive ? 'text-green-400' : 'text-red-400'}`}>
          {trend.positive ? '↑' : '↓'} {trend.value}
        </p>
      )}
    </div>
  )
}

export function OverviewCards({ timeRange = '24h' }: OverviewCardsProps) {
  const [auditStats, setAuditStats] = useState<any>(null)
  const [driftStats, setDriftStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Connect to SSE streams for real-time updates
    const complianceSource = new EventSource(config.getComplianceUrl('stream'))
    const driftSource = new EventSource(config.getDriftUrl('stream'))

    complianceSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setAuditStats(data)
        setLoading(false)
      } catch (error) {
        console.error('Error parsing compliance SSE data:', error)
      }
    }

    driftSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setDriftStats(data)
        setLoading(false)
      } catch (error) {
        console.error('Error parsing drift SSE data:', error)
      }
    }

    complianceSource.onerror = (error) => {
      console.error('Compliance SSE connection error:', error)
    }

    driftSource.onerror = (error) => {
      console.error('Drift SSE connection error:', error)
    }

    return () => {
      complianceSource.close()
      driftSource.close()
    }
  }, [])

  const totalRequests = auditStats?.total_requests || 0
  const avgLatency = auditStats?.avg_processing_time_ms || 0
  const successRate = auditStats?.by_status?.success || 0
  const totalRate = totalRequests > 0 ? ((successRate / totalRequests) * 100) : 0
  const driftAlertCount = driftStats?.total_alerts || 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="AVG LATENCY"
        value={`${avgLatency.toFixed(1)}ms`}
        loading={loading}
      />
      <MetricCard
        title="THROUGHPUT"
        value={totalRequests > 0 ? `${(totalRequests / 3600).toFixed(2)}k` : '0'}
        subtitle="req/hour"
        loading={loading}
      />
      <MetricCard
        title="SUCCESS RATE"
        value={`${totalRate.toFixed(1)}%`}
        trend={{ 
          value: totalRate >= 95 ? 'Healthy' : 'Check errors', 
          positive: totalRate >= 95 
        }}
        loading={loading}
      />
      <MetricCard
        title="AUDIT LOG EVENTS"
        value={totalRequests > 1000 ? `${(totalRequests / 1000000).toFixed(1)}M` : totalRequests.toString()}
        subtitle={driftAlertCount > 0 ? `${driftAlertCount} drift alerts` : 'SEC/FINRA/GDPR compliant'}
        loading={loading}
      />
    </div>
  )
}
