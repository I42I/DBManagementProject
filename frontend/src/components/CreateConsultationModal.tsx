import React, { useEffect, useState } from 'react'
import { patients, type PatientListItem } from '../lib/api/patients'
import { doctors, type DoctorListItem } from '../lib/api/doctors'
import { consultations, type NewConsultation } from '../lib/api/consultations'

type Props = {
  open: boolean
  onClose: () => void
  onCreated: (newId: string) => void  // callback après création
}

// Helper local : force un ISO UTC "Z" depuis un Date ou une string
function toISOZ(input: Date | string) {
  if (typeof input === 'string') {
    if (input.endsWith('Z')) return input
    const d = new Date(input)
    const utc = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
    return utc.toISOString().replace(/\.\d{3}Z$/, 'Z')
  }
  const utc = new Date(input.getTime() - input.getTimezoneOffset() * 60000)
  return utc.toISOString().replace(/\.\d{3}Z$/, 'Z')
}

export default function CreateConsultationModal({ open, onClose, onCreated }: Props) {
  const [loadingLists, setLoadingLists] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  const [plist, setPlist] = useState<PatientListItem[]>([])
  const [dlist, setDlist] = useState<DoctorListItem[]>([])

  // form state
  const [patientId, setPatientId] = useState('')
  const [doctorId, setDoctorId] = useState('')
  const [dateTime, setDateTime] = useState('') // "YYYY-MM-DDTHH:mm"
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    ;(async () => {
      try {
        setLoadingLists(true)
        setErr(null)
        const [p, d] = await Promise.all([
          patients.list(),
          doctors.list(),
        ])
        setPlist(p || [])
        setDlist(d || [])
        // valeurs par défaut si dispos
        if ((p || [])[0]?._id) setPatientId(p[0]._id)
        if ((d || [])[0]?._id) setDoctorId(d[0]._id)
        // maintenant (pré-rempli pour l'input)
        const now = new Date()
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
        setDateTime(now.toISOString().slice(0,16))
      } catch (e: any) {
        setErr(e.message ?? 'Impossible de charger les listes')
      } finally {
        setLoadingLists(false)
      }
    })()
  }, [open])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!patientId || !doctorId || !dateTime) return
    try {
      setSubmitting(true)
      setErr(null)
      const body: NewConsultation = {
        patient_id: patientId,
        doctor_id: doctorId,
        date_time: toISOZ(new Date(dateTime)),
        notes: notes || undefined,
      }
      const created = await consultations.createAndFetch(body)
      onCreated(created._id)
      onClose()
    } catch (e: any) {
      setErr(e.message ?? 'Échec de création')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  const disabled = submitting || loadingLists || !patientId || !doctorId || !dateTime

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl">
        <div className="p-6 border-b flex items-center justify-between">
          <h3 className="font-semibold text-lg">Créer une consultation</h3>
          <button className="btn-outline" onClick={onClose} type="button">Fermer</button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-3">
          {loadingLists && <p>Chargement…</p>}
          {err && <p className="text-red-600">{err}</p>}

          {!loadingLists && !err && (
            <>
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm mb-1">Patient</label>
                  <select
                    className="border rounded-xl px-3 py-2 w-full"
                    value={patientId}
                    onChange={e=>setPatientId(e.target.value)}
                    required
                  >
                    {plist.length === 0 && <option value="">Aucun patient</option>}
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
                    onChange={e=>setDoctorId(e.target.value)}
                    required
                  >
                    {dlist.length === 0 && <option value="">Aucun médecin</option>}
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
                  onChange={e=>setDateTime(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm mb-1">Notes (optionnel)</label>
                <textarea
                  className="border rounded-xl px-3 py-2 w-full"
                  rows={3}
                  value={notes}
                  onChange={e=>setNotes(e.target.value)}
                  placeholder="Observations, contexte…"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button type="button" className="btn-outline" onClick={onClose}>Annuler</button>
                <button className="btn-primary" type="submit" disabled={disabled}>
                  {submitting ? 'Création…' : 'Créer'}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}


