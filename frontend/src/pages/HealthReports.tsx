import React, { useEffect, useState } from 'react'
import { healthAuthorities, type HAReport, type HAStatus, type ReportType, type NewHAReport } from '../lib/api/health_authorities'

const STATUSES: HAStatus[] = ['draft', 'submitted', 'accepted', 'rejected']
const TYPES: ReportType[] = ['case_summary', 'disease_reporting', 'inventory', 'other']

type ModalProps = {
  open: boolean
  onClose: () => void
  onCreated: (id: string) => void
}

function toISODateUTC(d: string) {
  const dt = new Date(d)
  dt.setUTCHours(0, 0, 0, 0)
  return dt.toISOString()
}

function CreateHealthReportModal({ open, onClose, onCreated }: ModalProps) {
  const [facilityId, setFacilityId] = useState('')
  const [reportType, setReportType] = useState<ReportType>('case_summary')
  const [status, setStatus] = useState<HAStatus>('draft')
  const [periodStart, setPeriodStart] = useState(() => new Date().toISOString().slice(0, 10))
  const [periodEnd, setPeriodEnd] = useState(() => new Date().toISOString().slice(0, 10))
  const [externalRef, setExternalRef] = useState('')
  const [notes, setNotes] = useState('')
  const [submittedAt, setSubmittedAt] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  function reset() {
    setFacilityId('')
    setReportType('case_summary')
    setStatus('draft')
    const today = new Date().toISOString().slice(0, 10)
    setPeriodStart(today)
    setPeriodEnd(today)
    setExternalRef('')
    setNotes('')
    setSubmittedAt('')
    setErr(null)
  }

  useEffect(() => {
    if (!open) return
    reset()
  }, [open])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!facilityId.trim()) {
      setErr('facility_id requis (ObjectId Mongo)')
      return
    }
    if (!periodStart || !periodEnd) {
      setErr('Dates de période requises')
      return
    }
    if (periodEnd < periodStart) {
      setErr('La date de fin doit être >= date de début')
      return
    }

    const payload: NewHAReport = {
      facility_id: facilityId.trim(),
      report_type: reportType,
      period_start: toISODateUTC(periodStart),
      period_end: toISODateUTC(periodEnd),
      status,
      external_ref: externalRef || undefined,
      notes: notes || undefined,
      submitted_at: submittedAt ? toISODateUTC(submittedAt) : undefined,
    }

    try {
      setSubmitting(true); setErr(null)
      const created = await healthAuthorities.create(payload)
      onCreated(created._id)
      onClose()
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
          <h3 className="font-semibold text-lg">Nouveau rapport</h3>
          <button className="btn-outline" onClick={onClose}>Fermer</button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-4">
          {err && <p className="text-red-600 text-sm">{err}</p>}

          <div>
            <label className="block text-sm mb-1">facility_id (ObjectId)</label>
            <input
              className="border rounded-xl px-3 py-2 w-full"
              value={facilityId}
              onChange={e => setFacilityId(e.target.value)}
              placeholder="Ex: 6512bd43d9caa6e02c990b0a"
              required
            />
            <p className="text-xs text-slate-500 mt-1">Utilisez un ObjectId existant (facilities collection).</p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">Type de rapport</label>
              <select className="border rounded-xl px-3 py-2 w-full" value={reportType} onChange={e => setReportType(e.target.value as ReportType)}>
                {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1">Statut</label>
              <select className="border rounded-xl px-3 py-2 w-full" value={status} onChange={e => setStatus(e.target.value as HAStatus)}>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">Période début</label>
              <input className="border rounded-xl px-3 py-2 w-full" type="date" value={periodStart} onChange={e => setPeriodStart(e.target.value)} required />
            </div>
            <div>
              <label className="block text-sm mb-1">Période fin</label>
              <input className="border rounded-xl px-3 py-2 w-full" type="date" value={periodEnd} onChange={e => setPeriodEnd(e.target.value)} required />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">Référence externe (optionnel)</label>
              <input className="border rounded-xl px-3 py-2 w-full" value={externalRef} onChange={e => setExternalRef(e.target.value)} placeholder="N° dossier ministère" />
            </div>
            <div>
              <label className="block text-sm mb-1">Date de soumission (optionnel)</label>
              <input className="border rounded-xl px-3 py-2 w-full" type="date" value={submittedAt} onChange={e => setSubmittedAt(e.target.value)} />
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1">Notes (optionnel)</label>
            <textarea className="border rounded-xl px-3 py-2 w-full" rows={3} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Résumé, incidents, remarques..." />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-outline" onClick={onClose}>Annuler</button>
            <button className="btn-primary" type="submit" disabled={submitting}>{submitting ? 'Création…' : 'Créer'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function HealthReportsPage() {
  const [list, setList] = useState<HAReport[]>([])
  const [status, setStatus] = useState<HAStatus | ''>('')
  const [type, setType] = useState<ReportType | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  async function load(currentStatus: HAStatus | '', currentType: ReportType | '') {
    try {
      setLoading(true); setError(null)
      const params: Record<string, string> = {}
      if (currentStatus) params.status = currentStatus
      if (currentType) params.report_type = currentType
      const data = await healthAuthorities.list(Object.keys(params).length ? params as any : undefined)
      setList(data)
    } catch (e: any) {
      setError(e.message ?? 'Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(status, type) }, [status, type])

  function handleCreated(id: string) {
    setToast(`Rapport créé ✅ (${id})`)
    setOpen(false)
    load(status, type)
    setTimeout(() => setToast(null), 2500)
  }

  return (
    <div className="container py-10 space-y-6">
      <header className="flex flex-wrap items-center gap-3 justify-between">
        <div>
          <h2 className="h2">Rapports autorité de santé</h2>
          <p className="text-sm text-slate-600">Suivi des transmissions officielles vers le ministère.</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="border rounded-xl px-3 py-2 text-sm" value={type} onChange={e => setType(e.target.value as ReportType | '')}>
            <option value="">Tous les types</option>
            {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="border rounded-xl px-3 py-2 text-sm" value={status} onChange={e => setStatus(e.target.value as HAStatus | '')}>
            <option value="">Tous les statuts</option>
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button className="btn-primary" onClick={() => setOpen(true)}>Nouveau rapport</button>
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
                <th className="py-2">Type</th>
                <th>Période</th>
                <th>Statut</th>
                <th>Facility</th>
                <th>Réf. externe</th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-500">Aucun rapport</td>
                </tr>
              ) : (
                list.map(r => (
                  <tr key={r._id} className="border-t">
                    <td className="py-2">{r.report_type}</td>
                    <td>{new Date(r.period_start).toLocaleDateString()} → {new Date(r.period_end).toLocaleDateString()}</td>
                    <td>{r.status}</td>
                    <td>{r.facility_id}</td>
                    <td>{r.external_ref ?? '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <CreateHealthReportModal open={open} onClose={() => setOpen(false)} onCreated={handleCreated} />
    </div>
  )
}