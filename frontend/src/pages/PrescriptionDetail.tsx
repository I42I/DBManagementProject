import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { prescriptions, type PrescriptionFull } from '../lib/api/prescriptions'

// -------- helpers --------
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

// -------- composant principal --------
export default function PrescriptionDetail() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<PrescriptionFull | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    (async () => {
      try {
        setLoading(true)
        const doc = await prescriptions.getById(id)
        setData(doc)
      } catch (e: any) {
        setErr(e?.message ?? 'Erreur de chargement')
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  if (loading) return <div className="container py-10"><p>Chargement…</p></div>
  if (err) return <div className="container py-10"><p className="text-red-600">{err}</p></div>
  if (!data) return <div className="container py-10"><p>Prescription introuvable.</p></div>

  const pid = unwrapId(data.patient_id)
  const did = unwrapId(data.doctor_id)
  const cid = unwrapId(data.consultation_id)
  const created = fmtDateTime(unwrapDate(data.created_at))
  const updated = fmtDateTime(unwrapDate(data.updated_at))

  return (
    <div className="container py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="h2">Prescription</h2>
        <Link to="/services" className="btn-outline">← Retour</Link>
      </div>

      <div className="card p-6 space-y-3">
        <div className="grid md:grid-cols-2 gap-3 text-sm">
          <div><b>ID :</b> {unwrapId(data._id)}</div>
          <div><b>Date création :</b> {created}</div>
          <div><b>Dernière mise à jour :</b> {updated}</div>
          <div><b>Patient :</b> {pid}</div>
          <div><b>Médecin :</b> {did}</div>
          <div><b>Consultation :</b> {cid}</div>
        </div>

        {data.notes && <p className="text-sm"><b>Notes :</b> {data.notes}</p>}
      </div>

      <div className="card p-6">
        <h3 className="font-semibold mb-3">Médicaments prescrits</h3>
        {(!data.items || data.items.length === 0) ? (
          <p className="text-sm text-slate-600">Aucun médicament listé.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2">DCI</th>
                <th>Forme</th>
                <th>Posologie</th>
                <th>Durée (j)</th>
                <th>Contre-indications</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((m, i) => (
                <tr key={i} className="border-t">
                  <td className="py-2">{m.dci ?? '—'}</td>
                  <td>{m.forme ?? '—'}</td>
                  <td>{m.posologie ?? '—'}</td>
                  <td>{m.duree_j ?? '—'}</td>
                  <td>{m.contre_indications ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

