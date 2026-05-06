import React, { useState } from 'react'
import { submitRCA } from '../api/client'
import { VALID_CATEGORIES } from '../constants'

const field = (label, children, hint) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
    <label style={{
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 600,
      letterSpacing: '0.1em',
      color: 'var(--text-secondary)',
    }}>
      {label}
    </label>
    {children}
    {hint && (
      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{hint}</span>
    )}
  </div>
)

const inputStyle = {
  padding: '8px 10px',
  fontSize: 13,
  background: 'var(--bg-base)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)',
  width: '100%',
  transition: 'border-color 0.15s',
}

const textareaStyle = {
  ...inputStyle,
  resize: 'vertical',
  minHeight: 90,
  lineHeight: 1.6,
}

export default function RCAForm({ workitemId, onSuccess }) {
  const now = new Date()
  const oneHourAgo = new Date(now - 3600000)
  const fmt = d => d.toISOString().slice(0, 16)

  const [form, setForm] = useState({
    incident_start:      fmt(oneHourAgo),
    incident_end:        fmt(now),
    root_cause_category: '',
    fix_applied:         '',
    prevention_steps:    '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]           = useState(null)

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const handleSubmit = async () => {
    setError(null)
    if (!form.root_cause_category) return setError('Select a root cause category.')
    if (form.fix_applied.trim().length < 10) return setError('Fix applied must be at least 10 characters.')
    if (form.prevention_steps.trim().length < 10) return setError('Prevention steps must be at least 10 characters.')

    setSubmitting(true)
    try {
      await submitRCA(workitemId, {
        ...form,
        incident_start: new Date(form.incident_start).toISOString(),
        incident_end:   new Date(form.incident_end).toISOString(),
      })
      onSuccess()
    } catch (err) {
      const msg = err?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

      {/* Time range row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {field('INCIDENT START',
          <input
            type="datetime-local"
            value={form.incident_start}
            onChange={e => set('incident_start', e.target.value)}
            style={inputStyle}
          />
        )}
        {field('INCIDENT END',
          <input
            type="datetime-local"
            value={form.incident_end}
            onChange={e => set('incident_end', e.target.value)}
            style={inputStyle}
          />
        )}
      </div>

      {/* Category */}
      {field('ROOT CAUSE CATEGORY',
        <select
          value={form.root_cause_category}
          onChange={e => set('root_cause_category', e.target.value)}
          style={{ ...inputStyle, cursor: 'pointer' }}
        >
          <option value="">— select category —</option>
          {VALID_CATEGORIES.map(c => (
            <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
          ))}
        </select>
      )}

      {/* Fix applied */}
      {field(
        'FIX APPLIED',
        <textarea
          value={form.fix_applied}
          onChange={e => set('fix_applied', e.target.value)}
          placeholder="Describe what was done to resolve the incident..."
          style={textareaStyle}
        />,
        'Minimum 10 characters'
      )}

      {/* Prevention */}
      {field(
        'PREVENTION STEPS',
        <textarea
          value={form.prevention_steps}
          onChange={e => set('prevention_steps', e.target.value)}
          placeholder="What will prevent this from happening again?..."
          style={{ ...textareaStyle, minHeight: 80 }}
        />,
        'Minimum 10 characters'
      )}

      {/* Error */}
      {error && (
        <div style={{
          padding: '8px 12px',
          background: 'var(--p0-dim)',
          border: '1px solid var(--p0)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--p0)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
        }}>
          ✗ {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting}
        style={{
          padding: '10px 20px',
          background: submitting ? 'var(--bg-elevated)' : 'var(--green-dim)',
          border: `1px solid ${submitting ? 'var(--border)' : 'var(--green)'}`,
          borderRadius: 'var(--radius-sm)',
          color: submitting ? 'var(--text-muted)' : 'var(--green)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: '0.08em',
          transition: 'all 0.15s',
          alignSelf: 'flex-start',
        }}
      >
        {submitting ? 'SUBMITTING...' : '▸ SUBMIT RCA'}
      </button>
    </div>
  )
}
