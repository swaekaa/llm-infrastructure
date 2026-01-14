'use client'

import React, { useEffect, useState } from 'react'

interface Activity {
  id: string
  type: 'audit' | 'drift' | 'error'
  title: string
  description: string
  timestamp: string
}

export function RecentActivity() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Sample activity data
    const sampleActivities: Activity[] = [
      {
        id: '1',
        type: 'audit',
        title: 'Audit Log Created',
        description: 'Request to /api/v1/completion from tenant acme-corp',
        timestamp: '2 minutes ago',
      },
      {
        id: '2',
        type: 'drift',
        title: 'Drift Alert',
        description: 'Confidence score drift detected (0.85 → 0.82)',
        timestamp: '5 minutes ago',
      },
      {
        id: '3',
        type: 'audit',
        title: 'Audit Query',
        description: 'Compliance report generated for FINRA',
        timestamp: '12 minutes ago',
      },
      {
        id: '4',
        type: 'error',
        title: 'Error Logged',
        description: 'Rate limit exceeded for tenant finance-ai',
        timestamp: '18 minutes ago',
      },
      {
        id: '5',
        type: 'audit',
        title: 'Multi-Tenant Isolation',
        description: 'Tenant risk-mgmt accessed their audit logs',
        timestamp: '25 minutes ago',
      },
    ]
    setActivities(sampleActivities)
    setLoading(false)
  }, [])

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'audit':
        return '📋'
      case 'drift':
        return '⚠️'
      case 'error':
        return '❌'
      default:
        return '📌'
    }
  }

  const getActivityColor = (type: Activity['type']) => {
    switch (type) {
      case 'audit':
        return 'border-blue-500/20'
      case 'drift':
        return 'border-yellow-500/20'
      case 'error':
        return 'border-red-500/20'
      default:
        return 'border-slate-700'
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
        <p className="text-sm text-slate-400 mt-1">Latest audit and drift events</p>
      </div>

      {loading ? (
        <div className="text-center text-slate-400 py-8">Loading...</div>
      ) : (
        <div className="space-y-4">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className={`flex items-start gap-4 p-4 border border-l-2 rounded-lg bg-slate-950/50 ${getActivityColor(activity.type)}`}
            >
              <span className="text-2xl">{getActivityIcon(activity.type)}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{activity.title}</p>
                <p className="text-sm text-slate-400 mt-1 truncate">
                  {activity.description}
                </p>
                <p className="text-xs text-slate-500 mt-2">{activity.timestamp}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
