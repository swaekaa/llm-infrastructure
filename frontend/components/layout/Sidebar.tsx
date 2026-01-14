'use client'

import Link from 'next/link'
import React from 'react'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const menuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/audit-logs', label: 'Audit Logs', icon: '📋' },
  { href: '/drift-detection', label: 'Drift Detection', icon: '📈' },
  { href: '/compliance', label: 'Compliance', icon: '✅' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:relative w-64 h-screen bg-neutral-900 border-r border-neutral-800 transform md:transform-none transition-transform z-50 ${
          open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-neutral-800">
          <div className="text-xl font-bold text-amber-500">
            LLM<span className="text-white">infra</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="mt-8 px-4 space-y-2">
          {menuItems.map((item) => (
            <Link key={item.href} href={item.href}>
              <span className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-neutral-800 transition-colors text-slate-300 hover:text-white cursor-pointer">
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </span>
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 w-full p-4 border-t border-neutral-800 bg-black">
          <div className="text-xs text-slate-500">
            v1.0.0 • Production Ready
          </div>
        </div>
      </aside>
    </>
  )
}
