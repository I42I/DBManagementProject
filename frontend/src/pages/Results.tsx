import React, { useState } from 'react'
import { http } from '../lib/http'

// ---------- Types alignés sur /api/laboratories ----------
type LabTest = {
  code?: string
  name?: string
  status?: string
  result?: number | string
  unit?: string
  ref_range?: string
  abnormal?: boolean
}

type Laboratory = {
  _id: { $oid: string } | string
  patient_id: { $oid: string } | string
  doctor_id: { $oid: string } | string
  facility_id?: { $oid: string } | string
  appointment_id?: { $oid: string } | string
  status: 'ordered' | 'in_progress' | 'completed' | 'cancelled'
  date_ordered?: { $date: string } | string
  date_reported?: { $date: string } | string
  tests?: LabTest[]
  notes?: string
}

// ---------- Helpers pour “Extended JSON” Mongo ----------
function asHex24(v: string) {
  return /^[0-9a-f]{24}$/i.test(v.trim())
}
function unwrapId(v: any): string {
  return typeof v === 'string' ? v : (v?.$oid ?? String(v ?? ''))
}
function unwrapDate(v: any): string | undefined {
  if (!v) return undefined
  if (typeof v === 'string') return v
  const iso = v?.$date ?? v?.date ?? undefined
  return typeof iso === 'string' ? iso : undefined
}
function fmtDateTime(iso?: string) {
  return iso ? new Date(iso).toLocaleString() : '—'
}

// --------------------------------------------------------

export default function Results() {
  const [idOrCode, setIdOrCode] = useState('')     // on tape l'ID labo (ObjectId)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [data, setData] = useState<Laboratory | null>(null)

  async function fetchByLabId(id: string) {
    return http<Laboratory>(`/api/laboratories/${id}`)
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = idOrCode.trim()
    if (!q) return
    setLoading(true); setErr(null); setData(null)
    try {
      if (!asHex24(q)) {
        throw new Error("Veuillez saisir un ID valide (ObjectId Mongo sur 24 caractères hexadécimaux).")
      }
      const lab = await fetchByLabId(q)
      setData(lab)
    } catch (e: any) {
      setErr(e?.message ?? "Erreur de recherche")
    } finally {
      setLoading(false)
    }
  }

  const pid = unwrapId(data?.patient_id)
  const did = unwrapId(data?.doctor_id)
  const created = fmtDateTime(unwrapDate(data?.date_ordered))
  const reported = fmtDateTime(unwrapDate(data?.date_reported))

  return (
    <div className="container py-10">
      <h2 className="h2 mb-4">Consulter mes résultats</h2>

      <form onSubmit={onSubmit} className="card p-6 mb-6">
        <label className="block mb-2 font-medium">ID de résultat (Mongo ObjectId)</label>
        <div className="flex gap-2">
          <input
            className="border rounded-xl px-3 py-2 flex-1"
            placeholder="Ex: 6512bd43d9caa6e02c990b0a"
            value={idOrCode}
            onChange={e=>setIdOrCode(e.target.value)}
            aria-label="Identifiant du résultat de laboratoire"
          />
          <button className="btn-primary" disabled={loading}>
            {loading ? 'Chargement…' : 'Consulter'}
          </button>
        </div>
        {err && <p className="mt-3 text-sm text-red-600">{err}</p>}
      </form>

      {data && (
        <div className="card p-6 space-y-4">
          <h3 className="font-semibold text-lg">Résultat de laboratoire</h3>

          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div><b>ID résultat :</b> {unwrapId(data._id)}</div>
            <div><b>Statut :</b> {data.status}</div>
            <div><b>Patient :</b> {pid}</div>
            <div><b>Médecin :</b> {did}</div>
            <div><b>Commandé le :</b> {created}</div>
            <div><b>Rapporté le :</b> {reported}</div>
          </div>

          {data.notes && <p className="text-sm"><b>Notes :</b> {data.notes}</p>}

          <section>
            <h4 className="font-medium mb-2">Examens</h4>
            {(!data.tests || data.tests.length === 0) ? (
              <p className="text-sm text-slate-600">Aucun test listé.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left">
                    <th className="py-2">Test</th>
                    <th>Résultat</th>
                    <th>Unités</th>
                    <th>Référence</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tests.map((t, i) => (
                    <tr key={i} className="border-t">
                      <td className="py-2">{t.code ? `${t.code} — ` : ''}{t.name ?? '—'}</td>
                      <td>{t.result ?? '—'}{t.abnormal ? ' ⚠️' : ''}</td>
                      <td>{t.unit ?? '—'}</td>
                      <td>{t.ref_range ?? '—'}</td>
                      <td>{t.status ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      )}
    </div>
  )
}

