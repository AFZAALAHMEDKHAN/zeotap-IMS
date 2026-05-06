import React from 'react'

const STATUS_STYLES = {
  OPEN:          { color: 'var(--open)',          dot: true },
  INVESTIGATING: { color: 'var(--investigating)', dot: true },
  RESOLVED:      { color: 'var(--resolved)',      dot: false },
  CLOSED:        { color: 'var(--closed)',         dot: false },
}

export default function StatusBadge({ status }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.OPEN

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        fontWeight: 500,
        color: s.color,
        letterSpacing: '0.06em',
      }}
    >
      {s.dot && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: s.color,
            animation: 'pulse-dot 1.8s ease-in-out infinite',
            flexShrink: 0,
          }}
        />
      )}
      {status}
    </span>
  )
}
