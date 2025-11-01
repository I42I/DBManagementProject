import React, { useEffect, useState } from 'react'
import { appointments, toISOZ, type Appointment } from '../lib/api/appointments'
import CreateAppointmentModal from '../components/CreateAppointmentModal' // ⬅️ ajout

type Row = Appointment & {
  patient_identifier?: string
  patient_name?: string
}

export default function Appointments() {
  const [date, setDate] = useState<string>(() => {
    const d = new Date()
    return d.toISOString().slice(0, 10)
  })
  const [results, setResults] = useState<Row[]>([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  // état modale
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  async function loadForDay(dayISO: string) {
    setLoading(true)
    setErr(null)
    try {
      const day = new Date(dayISO)
      const start = new Date(day); start.setHours(0,0,0,0)
      const end   = new Date(day); end.setHours(23,59,59,999)
      const data = await appointments.list({
        date_from: toISOZ(start),
        date_to: toISOZ(end),
      })
      setResults(data as Row[])
    } catch (e: any) {
      setErr(e.message || 'Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadForDay(date) }, []) // initial
  // si tu veux recharger automatiquement quand la date change :
  useEffect(() => { loadForDay(date) }, [date])

  const search = (e: React.FormEvent) => {
    e.preventDefault()
    loadForDay(date)
  }

  function onCreated(id: string) {
    setToast('Rendez-vous créé ✅')
    setOpen(false)
    // rafraîchit la liste du jour
    loadForDay(date)
    setTimeout(() => setToast(null), 2000)
  }

  return (
    <div className="container py-10">
      <div className="flex items-center justify-between mb-4">
        <h2 className="h2">Prendre rendez-vous</h2>
        <button className="btn-primary" onClick={() => setOpen(true)}>Nouveau rendez-vous</button>
      </div>

      {toast && (
        <div className="mb-4 rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-2 text-sm text-emerald-800">
          {toast}
        </div>
      )}

      <form onSubmit={search} className="card p-6 grid md:grid-cols-4 gap-3 mb-6">
        <input
          className="border rounded-xl px-3 py-2 md:col-span-3"
          type="date"
          value={date}
          onChange={e => setDate(e.target.value)}
        />
        <button className="btn-primary" type="submit">Rechercher</button>
      </form>

      {loading && <p>Chargement…</p>}
      {err && <p className="text-red-600">{err}</p>}

      {!loading && !err && (
        <div className="card p-6">
          <h3 className="font-semibold mb-3">Rendez-vous du {new Date(date).toLocaleDateString()}</h3>

          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2">Patient</th>
                <th>Heure</th>
                <th>Statut</th>
                <th>Motif</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-gray-500">
                    Aucun rendez-vous ce jour.
                  </td>
                </tr>
              ) : (
                results.map(a => (
                  <tr key={a._id} className="border-t">
                    <td className="py-2">
                      {a.patient_identifier
                        ? `${a.patient_identifier} — ${a.patient_name ?? ''}`
                        : (a.patient_name ?? a.patient_id)}
                    </td>
                    <td>{new Date(a.date_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                    <td>{a.status}</td>
                    <td>{a.reason ?? '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modale création */}
      <CreateAppointmentModal
        open={open}
        onClose={() => setOpen(false)}
        onCreated={onCreated}
      />
    </div>
  )
}

