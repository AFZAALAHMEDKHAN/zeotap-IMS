import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { usePolling } from '../hooks/usePolling'
import { fetchHealth } from '../api/client'

export default function Header() {
  const { pathname } = useLocation()
  const { data: health } = usePolling(fetchHealth, 15000)
  const overall = health?.overall || 'unknown'

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      height: 52,
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      flexShrink: 0,
    }}>
      {/* Logo */}
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--text-primary)',
          letterSpacing: '0.1em',
        }}>
          ▸ IMS
        </span>
        <span style={{
          fontSize: 11,
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          letterSpacing: '0.05em',
        }}>
          INCIDENT MANAGEMENT SYSTEM
        </span>
      </Link>

      {/* Nav */}
      <nav style={{ display: 'flex', gap: 4 }}>
        {[
          { path: '/', label: 'DASHBOARD' },
          { path: '/signals', label: 'FIRE SIGNAL' },
        ].map(({ path, label }) => (
          <Link
            key={path}
            to={path}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: '0.08em',
              padding: '5px 12px',
              borderRadius: 'var(--radius-sm)',
              color: pathname === path ? 'var(--text-primary)' : 'var(--text-muted)',
              background: pathname === path ? 'var(--bg-elevated)' : 'transparent',
              border: pathname === path ? '1px solid var(--border)' : '1px solid transparent',
              transition: 'all 0.15s',
            }}
          >
            {label}
          </Link>
        ))}
      </nav>

      {/* Health indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-muted)',
          letterSpacing: '0.06em',
        }}>
          SYSTEM
        </span>
        <div style={{ display: 'flex', gap: 5 }}>
          {['postgres', 'mongodb', 'redis'].map(svc => {
            const ok = health?.[svc] === 'ok'
            return (
              <div
                key={svc}
                title={`${svc}: ${health?.[svc] || 'checking...'}`}
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: !health ? 'var(--text-muted)' : ok ? 'var(--green)' : 'var(--p0)',
                  animation: ok ? 'none' : 'pulse-dot 1s infinite',
                }}
              />
            )
          })}
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: overall === 'ok' ? 'var(--green)' : overall === 'degraded' ? 'var(--p1)' : 'var(--text-muted)',
          letterSpacing: '0.06em',
        }}>
          {overall.toUpperCase()}
        </span>
      </div>
    </header>
  )
}
