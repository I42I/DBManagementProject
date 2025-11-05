import React, { useEffect, useState } from 'react'
import { patients, type PatientListItem } from '../lib/api/patients'
import { doctors, type DoctorListItem } from '../lib/api/doctors'
import { appointments, toISOZ, type NewAppointment } from '../lib/api/appointments'

type Props = {
  open: boolean
  onClose: () => void
  onCreated: (id: string) => void
}

export default function CreateAppointmentModal({ open, onClose, onCreated }: Props) {
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  const [plist, setPlist] = useState<PatientListItem[]>([])
  const [dlist, setDlist] = useState<DoctorListItem[]>([])

  const [patientId, setPatientId] = useState('')
  const [doctorId, setDoctorId]   = useState('')
  const [dateTime, setDateTime]   = useState('')   // HTML datetime-local: YYYY-MM-DDTHH:mm
  const [reason, setReason]       = useState('')
  const [notes, setNotes]         = useState('')

  useEffect(() => {
    if (!open) return
    ;(async () => {
      try {
        setLoading(true); setErr(null)
        const [p, d] = await Promise.all([patients.list(), doctors.list()])
        setPlist(p); setDlist(d)

        if (p[0]?._id) setPatientId(p[0]._id)
        if (d[0]?._id) setDoctorId(d[0]._id)

        // valeur par défaut maintenant (locale) pour <input type="datetime-local">
        const now = new Date()
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
        setDateTime(now.toISOString().slice(0, 16))
      } catch (e: any) {
        setErr(e?.message ?? 'Impossible de charger les listes')
      } finally {
        setLoading(false)
      }
    })()
  }, [open])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!patientId || !doctorId || !dateTime) return
    try {
      setErr(null)
      const body: NewAppointment = {
        patient_id: patientId,
        doctor_id: doctorId,
        date_time: toISOZ(new Date(dateTime)), // convertit en ISO avec Z
        reason: reason || undefined,
        notes: notes || undefined,
      }
      const created = await appointments.createAndFetch(body)
      onCreated(created._id)
      onClose()
    } catch (e: any) {
      setErr(e?.message ?? 'Échec de création')
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl">
        <div className="p-6 border-b flex items-center justify-between">
          <h3 className="font-semibold text-lg">Nouveau rendez-vous</h3>
          <button className="btn-outline" onClick={onClose}>Fermer</button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-3">
          {loading && <p>Chargement…</p>}
          {err && <p className="text-red-600">{err}</p>}

          {!loading && !err && (
            <>
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm mb-1">Patient</label>
                  <select
                    className="border rounded-xl px-3 py-2 w-full"
                    value={patientId}
                    onChange={e => setPatientId(e.target.value)}
                    required
                  >
                    {plist.map(p => (
                      <option key={p._id} value={p._id}>
                        {`${p.identite?.prenom ?? ''} ${p.identite?.nom ?? ''}`.trim() || p._id}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-1">Médecin</label>
                  <select
                    className="border rounded-xl px-3 py-2 w-full"
                    value={doctorId}
                    onChange={e => setDoctorId(e.target.value)}
                    required
                  >
                    {dlist.map(d => (
                      <option key={d._id} value={d._id}>
                        {`${d.identite?.prenom ?? ''} ${d.identite?.nom ?? ''}`.trim() || d._id}
                        {d.specialites?.length ? ` — ${d.specialites.join(', ')}` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm mb-1">Date & heure</label>
                <input
                  type="datetime-local"
                  className="border rounded-xl px-3 py-2 w-full"
                  value={dateTime}
                  onChange={e => setDateTime(e.target.value)}
                  required
                />
              </div>

              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm mb-1">Motif (optionnel)</label>
                  <input
                    className="border rounded-xl px-3 py-2 w-full"
                    placeholder="Ex: Douleur thoracique"
                    value={reason}
                    onChange={e => setReason(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1">Notes (optionnel)</label>
                  <input
                    className="border rounded-xl px-3 py-2 w-full"
                    placeholder="Commentaires…"
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button type="button" className="btn-outline" onClick={onClose}>Annuler</button>
                <button className="btn-primary" type="submit">Créer</button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}
