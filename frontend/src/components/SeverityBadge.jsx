import React from 'react'

const COLORS = {
  P0: { bg: 'var(--p0-dim)', color: 'var(--p0)', border: 'var(--p0)' },
  P1: { bg: 'var(--p1-dim)', color: 'var(--p1)', border: 'var(--p1)' },
  P2: { bg: 'var(--p2-dim)', color: 'var(--p2)', border: 'var(--p2)' },
}

export default function SeverityBadge({ priority, size = 'md' }) {
  const c = COLORS[priority] || COLORS.P2
  const fontSize = size === 'sm' ? '10px' : size === 'lg' ? '13px' : '11px'
  const padding  = size === 'sm' ? '1px 5px' : size === 'lg' ? '3px 10px' : '2px 7px'

  return (
    <span
      style={{
        display: 'inline-block',
        fontFamily: 'var(--font-mono)',
        fontSize,
        fontWeight: 600,
        padding,
        borderRadius: 'var(--radius-sm)',
        background: c.bg,
        color: c.color,
        border: `1px solid ${c.border}`,
        letterSpacing: '0.05em',
        whiteSpace: 'nowrap',
      }}
    >
      {priority}
    </span>
  )
}
