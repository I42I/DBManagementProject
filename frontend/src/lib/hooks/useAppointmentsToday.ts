import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { appointments, toISOZ, type Appointment } from '../../lib/api/appointments'

type Row = Appointment & {
  patient_identifier?: string
  patient_name?: string
}

export function useAppointmentsToday() {
  const [data, setData] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // borne de la journée locale (00:00 → 23:59:59.999)
  const { startISO, endISO } = useMemo(() => {
    const now = new Date()
    const start = new Date(now); start.setHours(0, 0, 0, 0)
    const end   = new Date(now); end.setHours(23, 59, 59, 999)
    return { startISO: toISOZ(start), endISO: toISOZ(end) }
  }, [])

  const alive = useRef(true)
  useEffect(() => {
    return () => { alive.current = false } // évite setState après unmount
  }, [])

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await appointments.list({
        date_from: startISO,
        date_to: endISO,
      })
      if (alive.current) setData(list as Row[])
    } catch (e: any) {
      if (alive.current) setError(e?.message ?? 'Erreur')
    } finally {
      if (alive.current) setLoading(false)
    }
  }, [startISO, endISO])

  useEffect(() => {
    reload()
  }, [reload])

  return { data, loading, error, reload }
}
