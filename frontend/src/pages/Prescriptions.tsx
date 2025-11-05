import React, { useEffect, useState } from 'react'
import {
  prescriptions,
  type PrescriptionListItem,
  type NewPrescription,
} from '../lib/api/prescriptions'
import { patients, type PatientListItem } from '../lib/api/patients'
import { doctors, type DoctorListItem } from '../lib/api/doctors'
import {
  consultations,
  type ConsultationListItem, // ← existe grâce au patch (1a)
} from '../lib/api/consultations'
import { Link } from 'react-router-dom'

export default function Prescriptions() {
  const [list, setList] = useState<PrescriptionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  async function load() {
    try {
      setLoading(true)
      setErr(null)
      const data = await prescriptions.list()
      setList(data)
    } catch (e: any) {
      setErr(e?.message ?? 'Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function onCreated(id: string) {
    setToast('Prescription créée ✅')
    setOpen(false)
    load()
    setTimeout(() => setToast(null), 2000)
  }

  return (
    <div className="container py-10">
      <div className="flex items-center justify-between mb-6">
        <h2 className="h2">Prescriptions</h2>
        <button className="btn-primary" onClick={() => setOpen(true)}>
          Nouvelle prescription
        </button>
      </div>

      {toast && (
        <div className="mb-4 rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-2 text-sm text-emerald-800">
          {toast}
        </div>
      )}

      {loading && <p>Chargement…</p>}
      {err && <p className="text-red-600">{err}</p>}

      {!loading && !err && (
        <div className="card p-6 overflow-x-auto">
          <h3 className="font-semibold mb-3">Dernières prescriptions</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2">ID</th>
                <th>Patient</th>
                <th>Médecin</th>
                <th>Consultation</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-gray-500">
                    Aucune prescription
                  </td>
                </tr>
              ) : (
                list.map(p => (
                  <tr key={p._id} className="border-t">
                    <td className="py-2">{p._id}</td>
                    <td>{p.patient_id}</td>
                    <td>{p.doctor_id}</td>
                    <td>{p.consultation_id}</td>
                    <td>{p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}</td>
                    <td>
                      {/* prévois la page détail si tu veux */}
                      <Link className="text-primary" to={`/prescriptions/${p._id}`}>
                        Voir détail →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {open && (
        <CreatePrescriptionModal onClose={() => setOpen(false)} onCreated={onCreated} />
      )}
    </div>
  )
}

// ---------------------- Modal de création ----------------------

function CreatePrescriptionModal({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: (id: string) => void
}) {
  const [plist, setPlist] = useState<PatientListItem[]>([])
  const [dlist, setDlist] = useState<DoctorListItem[]>([])
  const [clist, setClist] = useState<ConsultationListItem[]>([])

  const [patientId, setPatientId] = useState('')
  const [doctorId, setDoctorId] = useState('')
  const [consultId, setConsultId] = useState('')
  const [notes, setNotes] = useState('')
  const [dci, setDci] = useState('')
  const [posologie, setPosologie] = useState('')

  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        setLoading(true)
        setErr(null)
        const [p, d, c] = await Promise.all([
          patients.list(),
          doctors.list(),
          consultations.list(), // renvoie des Consultation (ok pour un Select)
        ])
        setPlist(p); setDlist(d); setClist(c as ConsultationListItem[])
        if (p[0]?._id) setPatientId(p[0]._id)
        if (d[0]?._id) setDoctorId(d[0]._id)
        if (c[0]?._id) setConsultId(c[0]._id)
      } catch (e: any) {
        setErr(e?.message ?? 'Erreur de chargement des listes')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!patientId || !doctorId || !consultId || !dci || !posologie) return
    try {
      setErr(null)
      const body: NewPrescription = {
        patient_id: patientId,
        doctor_id: doctorId,
        consultation_id: consultId,
        items: [{ dci, posologie }],
        notes: notes || undefined,
      }
      const created = await prescriptions.createAndFetch(body)
      onCreated(created._id)
    } catch (e: any) {
      setErr(e?.message ?? 'Échec de création')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl">
        <div className="p-6 border-b flex items-center justify-between">
          <h3 className="font-semibold text-lg">Nouvelle prescription</h3>
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
                    onChange={e=>setPatientId(e.target.value)}
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
                    onChange={e=>setDoctorId(e.target.value)}
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
                <label className="block text-sm mb-1">Consultation</label>
                <select
                  className="border rounded-xl px-3 py-2 w-full"
                  value={consultId}
                  onChange={e=>setConsultId(e.target.value)}
                >
                  {clist.map(c => (
                    <option key={c._id} value={c._id}>
                      {c._id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm mb-1">Médicament (DCI)</label>
                <input
                  className="border rounded-xl px-3 py-2 w-full"
                  placeholder="Ex: Paracétamol"
                  value={dci}
                  onChange={e=>setDci(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm mb-1">Posologie</label>
                <input
                  className="border rounded-xl px-3 py-2 w-full"
                  placeholder="Ex: 500 mg, 3x/jour"
                  value={posologie}
                  onChange={e=>setPosologie(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm mb-1">Notes</label>
                <textarea
                  className="border rounded-xl px-3 py-2 w-full"
                  rows={2}
                  value={notes}
                  onChange={e=>setNotes(e.target.value)}
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button type="button" className="btn-outline" onClick={onClose}>
                  Annuler
                </button>
                <button className="btn-primary" type="submit">
                  Créer
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}
