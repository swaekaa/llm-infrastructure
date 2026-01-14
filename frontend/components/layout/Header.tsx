'use client'

import React, { useEffect, useState } from 'react'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <header className="border-b border-neutral-800 bg-black">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">LLM Infrastructure</h1>
            <p className="text-sm text-slate-400 mt-1">Production monitoring & compliance</p>
          </div>
        </div>
      </div>
    </header>
  )
}
