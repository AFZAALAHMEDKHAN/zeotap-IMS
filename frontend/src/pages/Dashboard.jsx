import React, { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { usePolling } from '../hooks/usePolling'
import { fetchWorkItems, fetchTimeseries } from '../api/client'
import SeverityBadge from '../components/SeverityBadge'
import StatusBadge from '../components/StatusBadge'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

// ── Timeseries chart ─────────────────────────────────────────
function SignalChart() {
  const { data } = usePolling(fetchTimeseries, 10000)
  const points = (data?.data || []).map(d => ({
    t: d.timestamp?.slice(11, 16) || '',
    count: d.count || 0,
  }))

  if (!points.length) return (
    <div style={{
      height: 80, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: 'var(--text-muted)',
      fontFamily: 'var(--font-mono)', fontSize: 11,
    }}>
      NO TIMESERIES DATA
    </div>
  )

  return (
    <ResponsiveContainer width="100%" height={80}>
      <AreaChart data={points} margin={{ top: 5, right: 0, left: -30, bottom: 0 }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#4d9fff" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#4d9fff" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="t" tick={{ fill: '#555966', fontSize: 10, fontFamily: 'IBM Plex Mono' }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fill: '#555966', fontSize: 10, fontFamily: 'IBM Plex Mono' }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ background: '#13151a', border: '1px solid #2a2d36', borderRadius: 4, fontFamily: 'IBM Plex Mono', fontSize: 11 }}
          labelStyle={{ color: '#8b909e' }}
          itemStyle={{ color: '#4d9fff' }}
        />
        <Area type="monotone" dataKey="count" stroke="#4d9fff" strokeWidth={1.5} fill="url(#areaGrad)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

// ── Stat card ────────────────────────────────────────────────
function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '14px 18px',
    }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 26, fontWeight: 600, color: color || 'var(--text-primary)', lineHeight: 1 }}>
        {value ?? '—'}
      </div>
    </div>
  )
}

// ── Incident row ─────────────────────────────────────────────
function IncidentRow({ item, onClick, index }) {
  const ago = formatDistanceToNow(new Date(item.created_at), { addSuffix: true })
  const borderColor = item.priority === 'P0' ? 'var(--p0)' : item.priority === 'P1' ? 'var(--p1)' : 'var(--border)'

  return (
    <div
      onClick={onClick}
      style={{
        display: 'grid',
        gridTemplateColumns: '56px 1fr 130px 130px 80px 90px',
        alignItems: 'center',
        gap: 12,
        padding: '11px 16px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderLeft: `3px solid ${borderColor}`,
        borderRadius: 'var(--radius-sm)',
        cursor: 'pointer',
        transition: 'background 0.12s',
        animation: `slideIn 0.2s ease ${index * 0.04}s both`,
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
      onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-surface)'}
    >
      <SeverityBadge priority={item.priority} />
      <div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 1 }}>
          {item.component_id}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          {item.id.slice(0, 8)}…
        </div>
      </div>
      <StatusBadge status={item.status} />
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
        {item.alert_type}
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', textAlign: 'right' }}>
        {item.signal_count}
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', textAlign: 'right' }}>
        {ago}
      </div>
    </div>
  )
}

// ── Dashboard ────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate()
  const fetchFn = useCallback(fetchWorkItems, [])
  const { data: items, loading, error } = usePolling(fetchFn, 5000)

  const all = items || []
  const p0  = all.filter(i => i.priority === 'P0').length
  const p1  = all.filter(i => i.priority === 'P1').length
  const open = all.filter(i => i.status === 'OPEN').length

  return (
    <div style={{ padding: '24px', maxWidth: 1100, margin: '0 auto' }}>

      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
            LIVE FEED
          </span>
          <span style={{
            width: 6, height: 6, borderRadius: '50%', background: 'var(--green)',
            animation: 'pulse-dot 1.5s infinite',
          }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--green)', letterSpacing: '0.06em' }}>
            AUTO-REFRESH 5s
          </span>
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 500, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          Active Incidents
        </h1>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
        <StatCard label="TOTAL ACTIVE"  value={all.length} />
        <StatCard label="P0 CRITICAL"   value={p0}  color={p0  > 0 ? 'var(--p0)' : undefined} />
        <StatCard label="P1 HIGH"       value={p1}  color={p1  > 0 ? 'var(--p1)' : undefined} />
        <StatCard label="OPEN"          value={open} color={open > 0 ? 'var(--open)' : undefined} />
      </div>

      {/* Timeseries chart */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        padding: '14px 16px 10px',
        marginBottom: 24,
      }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: 10 }}>
          SIGNAL VOLUME — LAST 60 MIN
        </div>
        <SignalChart />
      </div>

      {/* Column headers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '56px 1fr 130px 130px 80px 90px',
        gap: 12,
        padding: '6px 16px',
        marginBottom: 6,
      }}>
        {['SEVERITY', 'COMPONENT', 'STATUS', 'TYPE', 'SIGNALS', 'AGE'].map(h => (
          <div key={h} style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
            {h}
          </div>
        ))}
      </div>

      {/* Incident list */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 40, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
          LOADING...
        </div>
      )}
      {error && (
        <div style={{
          padding: 16, background: 'var(--p0-dim)', border: '1px solid var(--p0)',
          borderRadius: 'var(--radius-sm)', color: 'var(--p0)',
          fontFamily: 'var(--font-mono)', fontSize: 12,
        }}>
          ✗ Failed to load incidents. Is the backend running?
        </div>
      )}
      {!loading && !error && all.length === 0 && (
        <div style={{
          textAlign: 'center', padding: '48px 0',
          fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)',
        }}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>◉</div>
          ALL SYSTEMS NOMINAL
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {all.map((item, i) => (
          <IncidentRow
            key={item.id}
            item={item}
            index={i}
            onClick={() => navigate(`/incident/${item.id}`)}
          />
        ))}
      </div>
    </div>
  )
}
