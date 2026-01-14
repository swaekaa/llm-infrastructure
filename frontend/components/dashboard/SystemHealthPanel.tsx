'use client'

import React, { useEffect, useState } from 'react'
import { config } from '@/lib/config'

interface ServiceStatus {
  name: string
  status: 'OK' | 'WARNING' | 'ERROR'
  uptime: string
}

interface SystemHealthPanelProps {
  timeRange?: string
}

export function SystemHealthPanel({ timeRange = '24h' }: SystemHealthPanelProps) {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'Kafka Broker', status: 'OK', uptime: '99.96% uptime' },
    { name: 'LLM Processor', status: 'OK', uptime: '99.92% uptime' },
    { name: 'Audit Logger', status: 'OK', uptime: '100% uptime' },
    { name: 'Drift Detector', status: 'WARNING', uptime: '98.9% uptime' },
    { name: 'Compliance API', status: 'OK', uptime: '99.99% uptime' },
    { name: 'Database (Audit DB)', status: 'OK', uptime: '99.97% uptime' },
  ])

  const [systemStatus, setSystemStatus] = useState<'Operational' | 'Degraded' | 'Down'>('Operational')
  const [healthySummary, setHealthySummary] = useState('5/6')
  const [warningSummary, setWarningSummary] = useState('1/6')

  useEffect(() => {
    // Check service health periodically
    const checkHealth = async () => {
      try {
        // Check compliance API
        const complianceRes = await fetch(config.getComplianceUrl('health')).catch(() => null)
        const driftRes = await fetch(config.getDriftUrl('health')).catch(() => null)

        setServices((prev) =>
          prev.map((service) => {
            if (service.name === 'Compliance API') {
              return { ...service, status: complianceRes?.ok ? 'OK' : 'ERROR' }
            }
            if (service.name === 'Drift Detector') {
              return { ...service, status: driftRes?.ok ? 'OK' : 'WARNING' }
            }
            return service
          })
        )

        const okCount = services.filter((s) => s.status === 'OK').length
        const warningCount = services.filter((s) => s.status === 'WARNING').length
        const errorCount = services.filter((s) => s.status === 'ERROR').length

        setHealthySummary(`${okCount}/${services.length}`)
        setWarningSummary(`${warningCount}/${services.length}`)

        if (errorCount > 0) {
          setSystemStatus('Down')
        } else if (warningCount > 0) {
          setSystemStatus('Operational')
        } else {
          setSystemStatus('Operational')
        }
      } catch (error) {
        console.error('Health check error:', error)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 10000) // Every 10s
    return () => clearInterval(interval)
  }, [services.length])

  return (
    <div className="bg-black border border-neutral-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold text-white mb-6">System Health</h2>

      {/* System operational status */}
      <div className="mb-6 p-4 bg-green-950/20 border border-green-900 rounded-lg">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-green-400">✓</span>
          <h3 className="text-sm font-medium text-green-400">System {systemStatus}</h3>
        </div>
        <p className="text-xs text-slate-400">All critical components healthy</p>
      </div>

      {/* Service statuses */}
      <div className="space-y-3 mb-6">
        {services.map((service, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-3 bg-neutral-900/50 border border-neutral-800 rounded-lg"
          >
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                service.status === 'OK' ? 'bg-green-400' :
                service.status === 'WARNING' ? 'bg-yellow-400' :
                'bg-red-400'
              }`} />
              <span className="text-sm text-white">{service.name}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500">{service.uptime}</span>
              <span className={`px-2 py-1 text-xs font-medium rounded ${
                service.status === 'OK' ? 'bg-green-500/20 text-green-400' :
                service.status === 'WARNING' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {service.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-neutral-900/50 border border-neutral-800 rounded-lg text-center">
          <div className="text-2xl font-bold text-white">{healthySummary}</div>
          <div className="text-xs text-slate-400 mt-1">Healthy</div>
        </div>
        <div className="p-4 bg-neutral-900/50 border border-neutral-800 rounded-lg text-center">
          <div className="text-2xl font-bold text-yellow-400">{warningSummary}</div>
          <div className="text-xs text-slate-400 mt-1">Warnings</div>
        </div>
      </div>
    </div>
  )
}
