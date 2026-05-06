import React, { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { formatDistanceToNow, format } from 'date-fns'
import { usePolling } from '../hooks/usePolling'
import { fetchWorkItem, updateStatus } from '../api/client'
import SeverityBadge from '../components/SeverityBadge'
import StatusBadge from '../components/StatusBadge'
import RCAForm from '../components/RCAForm'
import { STATUS_TRANSITIONS } from '../constants'

// ── Section wrapper ───────────────────────────────────────────
function Section({ title, children, action }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-elevated)',
      }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
          {title}
        </span>
        {action}
      </div>
      <div style={{ padding: 16 }}>
        {children}
      </div>
    </div>
  )
}

// ── KV row ────────────────────────────────────────────────────
function KV({ label, value, mono }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, padding: '5px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ minWidth: 160, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em', paddingTop: 2 }}>
        {label}
      </div>
      <div style={{ fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)', fontSize: 13, color: 'var(--text-primary)', flex: 1 }}>
        {value}
      </div>
    </div>
  )
}

// ── Signal row ────────────────────────────────────────────────
function SignalRow({ signal, index }) {
  const [expanded, setExpanded] = useState(false)
  const ago = signal.received_at
    ? formatDistanceToNow(new Date(signal.received_at), { addSuffix: true })
    : '—'

  return (
    <div
      style={{
        borderBottom: '1px solid var(--border)',
        animation: `slideIn 0.15s ease ${index * 0.02}s both`,
      }}
    >
      <div
        onClick={() => setExpanded(e => !e)}
        style={{
          display: 'grid',
          gridTemplateColumns: '52px 1fr auto',
          alignItems: 'center',
          gap: 12,
          padding: '9px 12px',
          cursor: 'pointer',
          transition: 'background 0.1s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        <SeverityBadge priority={signal.severity} size="sm" />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {signal.error_message}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {ago}
        </span>
      </div>
      {expanded && (
        <div style={{ padding: '8px 12px 12px', background: 'var(--bg-elevated)' }}>
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--text-secondary)',
            margin: 0,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}>
            {JSON.stringify(signal.raw_payload || {}, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

// ── State transition button ────────────────────────────────────
function TransitionButton({ label, onClick, loading, danger }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        padding: '6px 14px',
        background: danger ? 'var(--p0-dim)' : 'var(--bg-elevated)',
        border: `1px solid ${danger ? 'var(--p0)' : 'var(--border-bright)'}`,
        borderRadius: 'var(--radius-sm)',
        color: danger ? 'var(--p0)' : 'var(--text-secondary)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: '0.06em',
        transition: 'all 0.15s',
        cursor: loading ? 'default' : 'pointer',
        opacity: loading ? 0.5 : 1,
      }}
      onMouseEnter={e => { if (!loading) e.currentTarget.style.borderColor = danger ? 'var(--p0)' : 'var(--accent)' }}
      onMouseLeave={e => { if (!loading) e.currentTarget.style.borderColor = danger ? 'var(--p0)' : 'var(--border-bright)' }}
    >
      {label}
    </button>
  )
}

// ── Incident Detail ───────────────────────────────────────────
export default function IncidentDetail() {
  const { id }    = useParams()
  const navigate  = useNavigate()
  const [transitioning, setTransitioning] = useState(false)
  const [transitionError, setTransitionError] = useState(null)
  const [showRCAForm, setShowRCAForm] = useState(false)

  const fetchFn = useCallback(() => fetchWorkItem(id), [id])
  const { data: item, loading, error, refresh } = usePolling(fetchFn, 8000)

  const doTransition = async (status) => {
    setTransitionError(null)
    setTransitioning(true)
    try {
      await updateStatus(id, status)
      await refresh()
    } catch (err) {
      const msg = err?.response?.data?.detail
      setTransitionError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setTransitioning(false)
    }
  }

  if (loading) return (
    <div style={{ padding: 40, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
      LOADING...
    </div>
  )

  if (error || !item) return (
    <div style={{ padding: 24 }}>
      <div style={{ color: 'var(--p0)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        ✗ Could not load incident {id}
      </div>
    </div>
  )

  const transitions = STATUS_TRANSITIONS[item.status] || []
  const canSubmitRCA = item.status !== 'OPEN' && item.status !== 'CLOSED' && !item.rca
  const createdAt = format(new Date(item.created_at), 'yyyy-MM-dd HH:mm:ss')
  const updatedAt = format(new Date(item.updated_at), 'yyyy-MM-dd HH:mm:ss')

  return (
    <div style={{ padding: 24, maxWidth: 960, margin: '0 auto' }}>

      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'none', border: 'none', color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.06em',
            cursor: 'pointer', padding: 0,
          }}
        >
          ← DASHBOARD
        </button>
        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>/</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
          {id.slice(0, 8)}…
        </span>
      </div>

      {/* Title row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <SeverityBadge priority={item.priority} size="lg" />
        <h1 style={{ fontSize: 20, fontWeight: 500, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
          {item.component_id}
        </h1>
        <StatusBadge status={item.status} />
        {item.mttr_minutes != null && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--green)', background: 'var(--green-dim)', border: '1px solid var(--green)', padding: '2px 8px', borderRadius: 'var(--radius-sm)' }}>
            MTTR {item.mttr_minutes} min
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

        {/* Details */}
        <Section title="INCIDENT DETAILS">
          <KV label="WORK ITEM ID"  value={item.id} mono />
          <KV label="COMPONENT"     value={item.component_id} mono />
          <KV label="ALERT TYPE"    value={item.alert_type} mono />
          <KV label="SIGNAL COUNT"  value={item.signal_count} mono />
          <KV label="CREATED"       value={createdAt} mono />
          <KV label="LAST UPDATED"  value={updatedAt} mono />
        </Section>

        {/* State machine */}
        <Section title="STATE MACHINE">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
              <StatusBadge status={item.status} />
              {transitions.length > 0 && (
                <>
                  <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>→</span>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {transitions.map(t => (
                      <TransitionButton
                        key={t}
                        label={t}
                        loading={transitioning}
                        danger={t === 'CLOSED'}
                        onClick={() => t === 'CLOSED' ? doTransition(t) : doTransition(t)}
                      />
                    ))}
                  </div>
                </>
              )}
              {item.status === 'CLOSED' && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                  Terminal state — incident closed.
                </span>
              )}
            </div>
          </div>
          {transitionError && (
            <div style={{
              marginTop: 10,
              padding: '8px 12px',
              background: 'var(--p0-dim)',
              border: '1px solid var(--p0)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--p0)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
            }}>
              ✗ {transitionError}
            </div>
          )}
        </Section>

        {/* RCA section */}
        <Section
          title="ROOT CAUSE ANALYSIS"
          action={
            canSubmitRCA && !showRCAForm ? (
              <button
                onClick={() => setShowRCAForm(true)}
                style={{
                  background: 'var(--green-dim)', border: '1px solid var(--green)',
                  borderRadius: 'var(--radius-sm)', color: 'var(--green)',
                  fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
                  padding: '3px 10px', letterSpacing: '0.06em', cursor: 'pointer',
                }}
              >
                + SUBMIT RCA
              </button>
            ) : null
          }
        >
          {item.rca ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              <KV label="CATEGORY"   value={item.rca.root_cause_category} mono />
              <KV label="START"      value={format(new Date(item.rca.incident_start), 'yyyy-MM-dd HH:mm:ss')} mono />
              <KV label="END"        value={format(new Date(item.rca.incident_end), 'yyyy-MM-dd HH:mm:ss')} mono />
              <KV label="FIX APPLIED" value={item.rca.fix_applied} />
              <KV label="PREVENTION" value={item.rca.prevention_steps} />
              <KV label="SUBMITTED"  value={format(new Date(item.rca.submitted_at), 'yyyy-MM-dd HH:mm:ss')} mono />
            </div>
          ) : showRCAForm ? (
            <RCAForm
              workitemId={id}
              onSuccess={() => { setShowRCAForm(false); refresh() }}
            />
          ) : (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', padding: '8px 0' }}>
              {item.status === 'OPEN'
                ? 'Move to INVESTIGATING before submitting an RCA.'
                : item.status === 'CLOSED'
                ? 'No RCA was submitted for this incident.'
                : 'No RCA submitted yet. Click "+ SUBMIT RCA" above.'}
            </div>
          )}
        </Section>

        {/* Raw signals */}
        <Section title={`RAW SIGNALS (${item.signals?.length || 0} shown, latest first)`}>
          {!item.signals?.length ? (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
              No signals linked yet.
            </div>
          ) : (
            <div style={{ margin: '-16px', overflow: 'hidden', borderRadius: 'var(--radius)' }}>
              {item.signals.map((s, i) => (
                <SignalRow key={s._id || i} signal={s} index={i} />
              ))}
            </div>
          )}
        </Section>
      </div>
    </div>
  )
}
