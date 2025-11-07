import React, { useEffect, useState } from 'react'
import { pharmacies, type Pharmacy, type PharmacyStatus, type NewPharmacy } from '../lib/api/pharmacies'
import { patients, type PatientListItem } from '../lib/api/patients'
import { doctors, type DoctorListItem } from '../lib/api/doctors'
import { prescriptions, type PrescriptionListItem } from '../lib/api/prescriptions'

const STATUSES: PharmacyStatus[] = ['requested', 'prepared', 'dispensed', 'cancelled']

type CreateModalProps = {
  open: boolean
  onClose: () => void
  onCreated: (id: string) => void
}

function CreatePharmacyModal({ open, onClose, onCreated }: CreateModalProps) {
  const [plist, setPlist] = useState<PatientListItem[]>([])
  const [dlist, setDlist] = useState<DoctorListItem[]>([])
  const [rxlist, setRxlist] = useState<PrescriptionListItem[]>([])
  const [patientId, setPatientId] = useState('')
  const [doctorId, setDoctorId] = useState('')
  const [prescriptionId, setPrescriptionId] = useState('')
  const [status, setStatus] = useState<PharmacyStatus>('requested')
  const [dci, setDci] = useState('')
  const [qty, setQty] = useState('1')
  const [posologie, setPosologie] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    ;(async () => {
      try {
        setLoading(true); setErr(null)
        const [p, d, rx] = await Promise.all([
          patients.list(),
          doctors.list(),
          prescriptions.list()
        ])
        setPlist(p); setDlist(d); setRxlist(rx)
        if (p[0]?._id) setPatientId(p[0]._id)
        if (d[0]?._id) setDoctorId(d[0]._id)
        if (rx[0]?._id) setPrescriptionId(rx[0]._id)
      } catch (e: any) {
        setErr(e?.message ?? 'Impossible de charger les listes')
      } finally {
        setLoading(false)
      }
    })()
  }, [open])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!patientId || !doctorId || !dci.trim()) return
    const qtyNum = Number(qty)
    if (!Number.isFinite(qtyNum) || qtyNum <= 0) {
      setErr('Quantité invalide')
      return
    }
    const payload: NewPharmacy = {
      patient_id: patientId,
      doctor_id: doctorId,
      prescription_id: prescriptionId || undefined,
      status,
      items: [{
        dci: dci.trim(),
        qty: qtyNum,
        posologie: posologie || undefined,
        notes: notes || undefined,
      }],
    }
    try {
      setSubmitting(true); setErr(null)
      const created = await pharmacies.create(payload)
      onCreated(created._id)
      onClose()
      setDci(''); setQty('1'); setPosologie(''); setNotes('')
    } catch (e: any) {
      setErr(e?.message ?? 'Échec de création')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl">
        <div className="p-6 border-b flex items-center justify-between">
          <h3 className="font-semibold text-lg">Nouvelle dispensation</h3>
          <button className="btn-outline" onClick={onClose}>Fermer</button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          {loading && <p>Chargement…</p>}
          {err && <p className="text-red-600 text-sm">{err}</p>}
          {!loading && !err && (
            <>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1">Patient</label>
                  <select className="border rounded-xl px-3 py-2 w-full" value={patientId} onChange={e => setPatientId(e.target.value)} required>
                    {plist.length === 0 && <option value="">Aucun patient</option>}
                    {plist.map(p => (
                      <option key={p._id} value={p._id}>
                        {(p.identite?.prenom ?? '') + ' ' + (p.identite?.nom ?? '') || p._id}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm mb-1">Médecin</label>
                  <select className="border rounded-xl px-3 py-2 w-full" value={doctorId} onChange={e => setDoctorId(e.target.value)} required>
                    {dlist.length === 0 && <option value="">Aucun médecin</option>}
                    {dlist.map(d => (
                      <option key={d._id} value={d._id}>
                        {(d.identite?.prenom ?? '') + ' ' + (d.identite?.nom ?? '') || d._id}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1">Ordonnance liée (optionnel)</label>
                  <select className="border rounded-xl px-3 py-2 w-full" value={prescriptionId} onChange={e => setPrescriptionId(e.target.value)}>
                    <option value="">—</option>
                    {rxlist.map(rx => (
                      <option key={rx._id} value={rx._id}>{rx._id}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm mb-1">Statut</label>
                  <select className="border rounded-xl px-3 py-2 w-full" value={status} onChange={e => setStatus(e.target.value as PharmacyStatus)}>
                    {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1">Médicament (DCI)</label>
                  <input className="border rounded-xl px-3 py-2 w-full" value={dci} onChange={e => setDci(e.target.value)} placeholder="Ex: Paracetamol 500mg" required />
                </div>
                <div>
                  <label className="block text-sm mb-1">Quantité</label>
                  <input className="border rounded-xl px-3 py-2 w-full" value={qty} onChange={e => setQty(e.target.value)} />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1">Posologie (optionnel)</label>
                  <input className="border rounded-xl px-3 py-2 w-full" value={posologie} onChange={e => setPosologie(e.target.value)} placeholder="1 comprimé matin / soir" />
                </div>
                <div>
                  <label className="block text-sm mb-1">Notes (optionnel)</label>
                  <input className="border rounded-xl px-3 py-2 w-full" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Observations du pharmacien" />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" className="btn-outline" onClick={onClose}>Annuler</button>
                <button className="btn-primary" type="submit" disabled={submitting}>{submitting ? 'Création…' : 'Créer'}</button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}

export default function PharmaciesPage() {
  const [list, setList] = useState<Pharmacy[]>([])
  const [status, setStatus] = useState<PharmacyStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  async function load(selectedStatus: PharmacyStatus | '') {
    try {
      setLoading(true); setError(null)
      const data = await pharmacies.list(selectedStatus ? { status: selectedStatus } : undefined)
      setList(data)
    } catch (e: any) {
      setError(e.message ?? 'Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(status) }, [status])

  function handleCreated(id: string) {
    setToast(`Dispensation créée ✅ (${id})`)
    setOpen(false)
    load(status)
    setTimeout(() => setToast(null), 2500)
  }

  return (
    <div className="container py-10 space-y-6">
      <header className="flex flex-wrap items-center gap-3 justify-between">
        <div>
          <h2 className="h2">Dispensations en pharmacie</h2>
          <p className="text-sm text-slate-600">Suivi des délivrances liées aux prescriptions.</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="border rounded-xl px-3 py-2 text-sm" value={status} onChange={e => setStatus(e.target.value as PharmacyStatus | '')}>
            <option value="">Tous les statuts</option>
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button className="btn-primary" onClick={() => setOpen(true)}>Nouvelle dispensation</button>
        </div>
      </header>

      {toast && <div className="rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-2 text-sm text-emerald-700">{toast}</div>}
      {loading && <p>Chargement…</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="card p-6 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2">Patient</th>
                <th>Médecin</th>
                <th>Statut</th>
                <th>Articles</th>
                <th>Délivré le</th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-500">Aucune dispensation</td>
                </tr>
              ) : (
                list.map(p => (
                  <tr key={p._id} className="border-t">
                    <td className="py-2">{p.patient_id}</td>
                    <td>{p.doctor_id}</td>
                    <td>{p.status}</td>
                    <td>{p.items?.map(it => `${it.dci} ×${it.qty}`).join(', ') ?? '—'}</td>
                    <td>{p.dispensed_at ? new Date(p.dispensed_at).toLocaleString() : '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <CreatePharmacyModal open={open} onClose={() => setOpen(false)} onCreated={handleCreated} />
    </div>
  )
}