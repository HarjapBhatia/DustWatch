import { useEffect, useState } from 'react'
import axios from 'axios'

import type { CityStats, ConstructionSite } from '../types'

export const useSites = () => {
  const [sites, setSites] = useState<ConstructionSite[]>([])
  const [stats, setStats] = useState<CityStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        const [sitesResponse, statsResponse] = await Promise.all([
          axios.get<ConstructionSite[]>('/api/sites'),
          axios.get<CityStats>('/api/stats')
        ])

        if (!isMounted) {
          return
        }

        setSites(sitesResponse.data)
        setStats(statsResponse.data)
      } catch (fetchError) {
        if (!isMounted) {
          return
        }

        const message = fetchError instanceof Error ? fetchError.message : 'Failed to load data'
        setError(message)
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchData()

    return () => {
      isMounted = false
    }
  }, [])

  return { sites, stats, loading, error }
}
