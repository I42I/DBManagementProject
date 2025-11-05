import React, { useState } from 'react'
import { useAppointmentsToday } from '../lib/hooks/useAppointmentsToday'
import CreateConsultationModal from '../components/CreateConsultationModal'

export default function Professionals() {
  const { data, loading, error, reload } = useAppointmentsToday()
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  function onCreated(_id: string) {
    setToast('Consultation créée ✅')
    reload()                 // ✅ rafraîchit la liste du jour sans recharger la page
    setTimeout(() => setToast(null), 2500)
  }

  return (
    <div className="container py-10">
      <div className="flex items-center justify-between mb-6">
        <h2 className="h2">Espace Professionnels</h2>
        <button className="btn-primary" onClick={() => setOpen(true)}>
          Créer une consultation
        </button>
      </div>

      {toast && (
        <div className="mb-4 rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-2 text-sm text-emerald-800">
          {toast}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6">
        <div className="card p-6 md:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">Rendez-vous du jour</h3>
            <button className="btn-outline text-sm" onClick={reload}>Rafraîchir</button>
          </div>

          {loading && <p>Chargement…</p>}
          {error && <p className="text-red-600">{error}</p>}

          {!loading && !error && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="py-2">Patient</th>
                  <th>Heure</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {data.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-gray-500">
                      Aucun rendez-vous aujourd’hui.
                    </td>
                  </tr>
                ) : (
                  data.map(a => (
                    <tr key={a._id} className="border-t">
                      <td className="py-2">
                        {a.patient_identifier
                          ? `${a.patient_identifier} — ${a.patient_name ?? ''}`
                          : (a.patient_name ?? a.patient_id)}
                      </td>
                      <td>
                        {new Date(a.date_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td>{a.status}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-3">Statistiques</h3>
          <ul className="space-y-2 text-sm">
            <li>Patients vus : <b>{data.length}</b></li>
            <li>En attente : <b>{data.filter(a => a.status === 'scheduled').length}</b></li>
            <li>Annulés : <b>{data.filter(a => a.status === 'cancelled').length}</b></li>
          </ul>
        </div>
      </div>

      <CreateConsultationModal
        open={open}
        onClose={() => setOpen(false)}
        onCreated={onCreated}
      />
    </div>
  )
}
