import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Polls an async fetch function at `interval` ms.
 * Returns { data, loading, error, refresh }.
 * Stops polling when the component unmounts.
 */
export function usePolling(fetchFn, interval = 5000) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const timerRef              = useRef(null)
  const mountedRef            = useRef(true)

  const fetch = useCallback(async () => {
    try {
      const result = await fetchFn()
      if (mountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (mountedRef.current) setError(err)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [fetchFn])

  useEffect(() => {
    mountedRef.current = true
    fetch()
    timerRef.current = setInterval(fetch, interval)
    return () => {
      mountedRef.current = false
      clearInterval(timerRef.current)
    }
  }, [fetch, interval])

  return { data, loading, error, refresh: fetch }
}
