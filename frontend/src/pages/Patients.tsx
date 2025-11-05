// src/pages/Patients.tsx
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { patients, type PatientListItem, type NewPatient } from '../lib/api/patients'

const DEV = import.meta.env.DEV

// helper: force ISO UTC avec 'Z' (minuit local → Z)
function toISOZ(input: string | Date) {
  if (typeof input === 'string') {
    if (input.endsWith('Z')) return input
    const dt = new Date(input)
    const utc = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000)
    return utc.toISOString().replace(/\.\d{3}Z$/, 'Z')
  }
  const utc = new Date(input.getTime() - input.getTimezoneOffset() * 60000)
  return utc.toISOString().replace(/\.\d{3}Z$/, 'Z')
}

function formatName(p: PatientListItem) {
  const prenom = p.identite?.prenom ?? ''
  const nom = p.identite?.nom ?? ''
  const full = `${prenom} ${nom}`.trim()
  return full || '—'
}

export default function Patients() {
  // --- liste ---
  const [results, setResults] = useState<PatientListItem[]>([])
  const [list, setList] = useState<PatientListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  // --- form ajout rapide (dev) ---
  const [prenom, setPrenom] = useState('')
  const [nom, setNom] = useState('')
  const [dateN, setDateN] = useState('') // yyyy-mm-dd
  const [sexe, setSexe] = useState<'M' | 'F' | 'X'>('M')
  const [phone, setPhone] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function load() {
    try {
      setLoading(true)
      setError(null)
      const data = await patients.list()
      setList(data)
    } catch (e: any) {
      setError(e.message ?? 'Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`Voulez-vous vraiment supprimer le patient ${name} ?`)) return
    try {
      await patients.delete(id)
      load() // Rafraîchir la liste
    } catch (e: any) {
      setError(e.message || 'Erreur lors de la suppression')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (submitting) return
    if (!prenom.trim() || !nom.trim() || !dateN) return

    const body: NewPatient = {
      identite: {
        prenom: prenom.trim(),
        nom: nom.trim(),
        date_naissance: toISOZ(`${dateN}T00:00:00`),
        sexe,
      },
      contacts: phone ? { phone: phone.trim() } : undefined,
    }

    try {
      setSubmitting(true)
      setError(null)
      await patients.createAndFetch(body)
      // reset + reload
      setPrenom(''); setNom(''); setDateN(''); setSexe('M'); setPhone('')
      await load()
    } catch (e: any) {
      setError(e.message ?? 'Erreur à la création')
    } finally {
      setSubmitting(false)
    }
  }

  const tips: string[] = [
    "Apportez votre pièce d’identité et carnet de santé.",
    "Arrivez 15 minutes en avance pour les formalités.",
    "En cas d’urgence, appelez les numéros officiels."
  ]

  return (
    <div className="container py-10 space-y-8">
      {/* Bandeau haut */}
      <div>
        <h2 className="h2 mb-4">Espace Patients</h2>
        <p className="text-slate-600 mb-6">
          Une interface simple pour tous : prenez rendez-vous, suivez vos soins et accédez à vos résultats.
        </p>

        <div className="grid md:grid-cols-3 gap-6 mb-10">
          <div className="card p-6">
            <h3 className="font-semibold mb-2">Prendre rendez-vous</h3>
            <p className="text-sm text-slate-600 mb-3">Choisissez la date, le lieu et le spécialiste.</p>
            <Link to="/appointments" className="btn-primary">Commencer</Link>
          </div>
          <div className="card p-6">
            <h3 className="font-semibold mb-2">Résultats d’analyses</h3>
            <p className="text-sm text-slate-600 mb-3">Accédez rapidement à vos résultats.</p>
            <Link to="/results" className="btn-outline">Consulter</Link>
          </div>
          <div className="card p-6">
            <h3 className="font-semibold mb-2">Ordonnances</h3>
            <p className="text-sm text-slate-600 mb-3">Retrouvez vos prescriptions et alertes.</p>
            <Link to="/services" className="btn-outline">Voir</Link>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-3">Conseils utiles</h3>
          <ul className="list-disc pl-5 space-y-2 text-sm">
            {tips.map(t => <li key={t}>{t}</li>)}
          </ul>
        </div>
      </div>

      {/* Annuaire patients + formulaire dev */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Formulaire dev (masqué en prod) */}
        {DEV && (
          <form onSubmit={onSubmit} className="card p-6 md:col-span-1 space-y-3">
            <h3 className="font-semibold">Ajouter un patient (dev)</h3>
            <input className="border rounded-xl px-3 py-2" placeholder="Prénom"
              value={prenom} onChange={e => setPrenom(e.target.value)} />
            <input className="border rounded-xl px-3 py-2" placeholder="Nom"
              value={nom} onChange={e => setNom(e.target.value)} />
            <input className="border rounded-xl px-3 py-2" type="date"
              value={dateN} onChange={e => setDateN(e.target.value)} />
            <select className="border rounded-xl px-3 py-2"
              value={sexe} onChange={e => setSexe(e.target.value as any)}>
              <option value="M">M</option>
              <option value="F">F</option>
              <option value="X">X</option>
            </select>
            <input className="border rounded-xl px-3 py-2" placeholder="Téléphone (optionnel)"
              value={phone} onChange={e => setPhone(e.target.value)} />
            <button className="btn-primary w-full" disabled={submitting}>
              {submitting ? 'Ajout…' : 'Ajouter'}
            </button>
            {error && <p className="text-red-600 text-sm">{error}</p>}
          </form>
        )}

        {/* Liste */}
        <div className="card p-6 md:col-span-2">
          <h3 className="font-semibold mb-3">Annuaire des patients</h3>
          {loading ? (
            <p>Chargement…</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="py-2">Nom</th>
                  <th>Date de naissance</th>
                  <th>Sexe</th>
                  <th>Téléphone</th>
                </tr>
              </thead>
              <tbody>
                {list.length === 0 ? (
                  <tr><td colSpan={4} className="py-6 text-center text-gray-500">Aucun patient</td></tr>
                ) : list.map(p => (
                  <tr key={p._id} className="border-t">
                    <td className="py-2">{formatName(p)}</td>
                    <td>{p.identite.sexe}</td>
                    <td>{p.identite.date_naissance?.split('T')[0]}</td>
                    <td className="text-right">
                      <button
                        onClick={() => handleDelete(p._id, formatName(p))}
                        className="text-xs text-red-600 hover:underline"
                      >
                        Supprimer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && error && <p className="text-red-600 text-sm mt-3">{error}</p>}
        </div>
      </div>
    </div>
  )
}
