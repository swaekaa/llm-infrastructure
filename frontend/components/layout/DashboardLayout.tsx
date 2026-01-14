'use client'

import React, { ReactNode } from 'react'
import { Header } from './Header'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface DashboardLayoutProps {
  children: ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => {}} />

      {/* Navigation Tabs */}
      <div className="border-b border-neutral-800">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-8">
            <Link href="/dashboard">
              <span
                className={`inline-block py-4 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  pathname === '/dashboard'
                    ? 'border-white text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Overview
              </span>
            </Link>
            <Link href="/audit-logs">
              <span
                className={`inline-block py-4 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  pathname === '/audit-logs'
                    ? 'border-white text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Audit Logs
              </span>
            </Link>
            <Link href="/drift-detection">
              <span
                className={`inline-block py-4 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  pathname === '/drift-detection'
                    ? 'border-white text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Drift Detection
              </span>
            </Link>
            <Link href="/compliance">
              <span
                className={`inline-block py-4 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  pathname === '/compliance'
                    ? 'border-white text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Compliance
              </span>
            </Link>
          </nav>
        </div>
      </div>

      {/* Page Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  )
}
