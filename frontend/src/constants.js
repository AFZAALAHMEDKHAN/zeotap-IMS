export const VALID_CATEGORIES = [
  'DATABASE_FAILURE',
  'CACHE_FAILURE',
  'NETWORK_ISSUE',
  'APPLICATION_BUG',
  'INFRASTRUCTURE',
  'THIRD_PARTY',
  'HUMAN_ERROR',
  'UNKNOWN',
]

export const STATUS_TRANSITIONS = {
  OPEN:          ['INVESTIGATING'],
  INVESTIGATING: ['RESOLVED', 'OPEN'],
  RESOLVED:      ['CLOSED', 'INVESTIGATING'],
  CLOSED:        [],
}

export const PRIORITY_LABELS = {
  P0: 'Critical',
  P1: 'High',
  P2: 'Warning',
}
