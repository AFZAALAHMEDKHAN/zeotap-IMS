import React, { useState } from 'react'
import { ingestSignal } from '../api/client'

const PRESETS = [
  {
    label: 'RDBMS Outage',
    color: 'var(--p0)',
    payload: { component_id: 'RDBMS_PRIMARY', error_message: 'Connection refused — primary database unreachable', severity: 'P0', raw_payload: { host: 'rdbms-primary.internal', error_code: 500, latency_ms: 9999 } },
  },
  {
    label: 'Cache Failure',
    color: 'var(--p2)',
    payload: { component_id: 'CACHE_CLUSTER_01', error_message: 'Cache miss rate spike — Redis connection timeout', severity: 'P2', raw_payload: { host: 'redis-cluster-01.internal', error_code: 503, miss_rate: 0.98 } },
  },
  {
    label: 'API Gateway',
    color: 'var(--p1)',
    payload: { component_id: 'API_GATEWAY', error_message: '5xx error rate exceeds 10% threshold', severity: 'P1', raw_payload: { host: 'api-gateway.internal', error_code: 503, error_rate: 0.12 } },
  },
  {
    label: 'MCP Host',
    color: 'var(--p1)',
    payload: { component_id: 'MCP_HOST_01', error_message: 'MCP host unresponsive — health check failed', severity: 'P1', raw_payload: { host: 'mcp-host-01.internal', error_code: 502 } },
  },
  {
    label: 'Queue Backlog',
    color: 'var(--p1)',
    payload: { component_id: 'QUEUE_KAFKA_01', error_message: 'Consumer lag exceeds 50,000 messages', severity: 'P1', raw_payload: { host: 'kafka-01.internal', consumer_lag: 52400 } },
  },
]

const inputStyle = {
  padding: '8px 10px',
  fontSize: 13,
  background: 'var(--bg-base)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-mono)',
  width: '100%',
}

function FieldLabel({ children }) {
  return (
    <label style={{
      fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
      letterSpacing: '0.1em', color: 'var(--text-muted)',
    }}>
      {children}
    </label>
  )
}

export default function SignalFire() {
  const [form, setForm] = useState({
    component_id: '',
    error_message: '',
    severity: 'P1',
    raw_payload: '{}',
  })
  const [burst, setBurst] = useState(1)
  const [sending, setSending] = useState(false)
  const [log, setLog] = useState([])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const addLog = (msg, ok) =>
    setLog(l => [{ msg, ok, ts: new Date().toLocaleTimeString() }, ...l].slice(0, 40))

  const fire = async (payload, count = 1) => {
    setSending(true)
    let ok = 0, fail = 0
    const tasks = Array.from({ length: count }, () =>
      ingestSignal(payload).then(() => ok++).catch(() => fail++)
    )
    await Promise.all(tasks)
    addLog(
      `Fired ${count}x ${payload.component_id} [${payload.severity}] — ${ok} accepted, ${fail} failed`,
      fail === 0
    )
    setSending(false)
  }

  const handleSubmit = async () => {
    if (!form.component_id || !form.error_message) return
    let raw = {}
    try { raw = JSON.parse(form.raw_payload) } catch { raw = {} }
    await fire({ ...form, raw_payload: raw }, burst)
  }

  const handlePreset = async (preset) => {
    await fire(preset.payload, burst)
  }

  return (
    <div style={{ padding: 24, maxWidth: 960, margin: '0 auto' }}>

      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: 4 }}>
          SIGNAL INJECTOR
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 500, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          Fire Signals
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          Manually inject signals to simulate incidents. Watch the dashboard update in real time.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>

        {/* Left: custom form */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '10px 16px',
            borderBottom: '1px solid var(--border)',
            background: 'var(--bg-elevated)',
            fontFamily: 'var(--font-mono)', fontSize: 10,
            fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-muted)',
          }}>
            CUSTOM SIGNAL
          </div>
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <FieldLabel>COMPONENT ID</FieldLabel>
              <input
                style={inputStyle}
                placeholder="e.g. RDBMS_PRIMARY, CACHE_CLUSTER_01"
                value={form.component_id}
                onChange={e => set('component_id', e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <FieldLabel>ERROR MESSAGE</FieldLabel>
              <input
                style={inputStyle}
                placeholder="Describe the error..."
                value={form.error_message}
                onChange={e => set('error_message', e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <FieldLabel>SEVERITY</FieldLabel>
                <select
                  value={form.severity}
                  onChange={e => set('severity', e.target.value)}
                  style={{ ...inputStyle, cursor: 'pointer' }}
                >
                  <option value="P0">P0 — Critical</option>
                  <option value="P1">P1 — High</option>
                  <option value="P2">P2 — Warning</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <FieldLabel>BURST COUNT</FieldLabel>
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={burst}
                  onChange={e => setBurst(Math.max(1, Math.min(500, parseInt(e.target.value) || 1)))}
                  style={inputStyle}
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <FieldLabel>RAW PAYLOAD (JSON)</FieldLabel>
              <textarea
                value={form.raw_payload}
                onChange={e => set('raw_payload', e.target.value)}
                style={{ ...inputStyle, resize: 'vertical', minHeight: 72, lineHeight: 1.5 }}
              />
            </div>

            <button
              onClick={handleSubmit}
              disabled={sending || !form.component_id || !form.error_message}
              style={{
                padding: '9px 16px',
                background: sending ? 'var(--bg-elevated)' : 'var(--accent-dim)',
                border: `1px solid ${sending ? 'var(--border)' : 'var(--accent)'}`,
                borderRadius: 'var(--radius-sm)',
                color: sending ? 'var(--text-muted)' : 'var(--accent)',
                fontFamily: 'var(--font-mono)', fontSize: 12,
                fontWeight: 600, letterSpacing: '0.08em',
                transition: 'all 0.15s',
                opacity: !form.component_id || !form.error_message ? 0.4 : 1,
              }}
            >
              {sending ? 'SENDING...' : `▸ FIRE ${burst > 1 ? `×${burst}` : 'SIGNAL'}`}
            </button>
          </div>
        </div>

        {/* Right: presets + log */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Presets */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '10px 16px',
              borderBottom: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              fontFamily: 'var(--font-mono)', fontSize: 10,
              fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-muted)',
            }}>
              PRESET SCENARIOS
            </div>
            <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
              {PRESETS.map(p => (
                <button
                  key={p.label}
                  onClick={() => handlePreset(p)}
                  disabled={sending}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '9px 12px',
                    background: 'var(--bg-elevated)',
                    border: `1px solid var(--border)`,
                    borderLeft: `3px solid ${p.color}`,
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)', fontSize: 11,
                    transition: 'all 0.12s',
                    opacity: sending ? 0.5 : 1,
                    textAlign: 'left',
                  }}
                  onMouseEnter={e => { if (!sending) e.currentTarget.style.background = 'var(--bg-hover)' }}
                  onMouseLeave={e => { if (!sending) e.currentTarget.style.background = 'var(--bg-elevated)' }}
                >
                  <span>{p.label}</span>
                  <span style={{ color: p.color, fontSize: 10 }}>
                    {burst > 1 ? `×${burst}` : '×1'} ▸
                  </span>
                </button>
              ))}
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                Burst count from the form applies to presets too.
              </p>
            </div>
          </div>

          {/* Activity log */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '10px 16px',
              borderBottom: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              fontFamily: 'var(--font-mono)', fontSize: 10,
              fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-muted)',
            }}>
              ACTIVITY LOG
            </div>
            <div style={{ padding: 12, minHeight: 80, maxHeight: 200, overflowY: 'auto' }}>
              {log.length === 0 ? (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                  No activity yet. Fire a signal above.
                </div>
              ) : log.map((entry, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex', gap: 10, alignItems: 'flex-start',
                    padding: '4px 0',
                    borderBottom: i < log.length - 1 ? '1px solid var(--border)' : 'none',
                    animation: i === 0 ? 'fadeIn 0.2s ease' : 'none',
                  }}
                >
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {entry.ts}
                  </span>
                  <span style={{
                    fontFamily: 'var(--font-mono)', fontSize: 11,
                    color: entry.ok ? 'var(--green)' : 'var(--p0)',
                    lineHeight: 1.5,
                  }}>
                    {entry.ok ? '✓' : '✗'} {entry.msg}
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
