import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || ''

const client = axios.create({
  baseURL: BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Work Items ──────────────────────────────────────────────
export const fetchWorkItems = () =>
  client.get('/api/v1/workitems').then(r => r.data)

export const fetchWorkItem = (id) =>
  client.get(`/api/v1/workitems/${id}`).then(r => r.data)

export const updateStatus = (id, status) =>
  client.patch(`/api/v1/workitems/${id}/status`, { status }).then(r => r.data)

// ── RCA ─────────────────────────────────────────────────────
export const fetchRCA = (id) =>
  client.get(`/api/v1/workitems/${id}/rca`).then(r => r.data)

export const submitRCA = (id, payload) =>
  client.post(`/api/v1/workitems/${id}/rca`, payload).then(r => r.data)

// ── Signals ─────────────────────────────────────────────────
export const ingestSignal = (payload) =>
  client.post('/api/v1/signals', payload).then(r => r.data)

// ── Observability ────────────────────────────────────────────
export const fetchHealth = () =>
  client.get('/health').then(r => r.data)

export const fetchTimeseries = () =>
  client.get('/api/v1/metrics/timeseries').then(r => r.data)
