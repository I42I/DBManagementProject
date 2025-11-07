import React, { useState, useEffect } from 'react'
import { consultations, toISOZ, type ConsultationListItem } from '../lib/api/consultations'
import CreateConsultationModal from '../components/CreateConsultationModal'
import { appointments, type Appointment } from '../lib/api/appointments'

// Ajout des champs enrichis par le backend
type ConsultationRow = ConsultationListItem & {
  patient_name?: string
  doctor_name?: string
}

export default function Professionals() {
  // --- États pour la date et les données ---
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  // SUPPRESSION de la variable 'data' redondante
  const [consultationData, setConsultationData] = useState<ConsultationRow[]>([])
  const [appointmentData, setAppointmentData] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // --- États pour la modale et les notifications ---
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  // --- Fonction pour charger les données d'un jour donné ---
  async function loadForDay(dayISO: string) {
    setLoading(true)
    setError(null)
    try {
      const day = new Date(dayISO)
      const start = new Date(day); start.setUTCHours(0, 0, 0, 0)
      const end = new Date(day); end.setUTCHours(23, 59, 59, 999)

      // Charger les deux listes en parallèle
      const [consults, appts] = await Promise.all([
        consultations.list({ date_from: toISOZ(start), date_to: toISOZ(end) }),
        appointments.list({ date_from: toISOZ(start), date_to: toISOZ(end) })
      ]);

      setConsultationData(consults as ConsultationRow[])
      setAppointmentData(appts)
    } catch (e: any) {
      setError(e.message || 'Erreur lors du chargement des données')
    } finally {
      setLoading(false)
    }
  }

  // --- Chargement initial et lors du changement de date ---
  useEffect(() => {
    loadForDay(date)
  }, [date])

  function onCreated(_id: string) {
    setToast('Consultation créée ✅')
    setOpen(false)
    loadForDay(date) // Rafraîchit la liste
    setTimeout(() => setToast(null), 2500)
  }

  const totalAppointments = appointmentData.length
  const pendingAppointments = appointmentData.filter(a =>
    a.status === 'scheduled' || a.status === 'checked_in'
  ).length
  const completedAppointments = appointmentData.filter(a => a.status === 'completed').length
  const cancelledAppointments = appointmentData.filter(a => a.status === 'cancelled').length

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
            <h3 className="font-semibold">Consultations du {new Date(date).toLocaleDateString()}</h3>
            <form className="flex items-center gap-2">
              <input
                type="date"
                className="border rounded-xl px-3 py-1.5 text-sm"
                value={date}
                onChange={e => setDate(e.target.value)}
              />
              <button type="button" className="btn-outline text-sm" onClick={() => loadForDay(date)}>Rafraîchir</button>
            </form>
          </div>

          {loading && <p>Chargement…</p>}
          {error && <p className="text-red-600">{error}</p>}

          {!loading && !error && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="py-2">Patient</th>
                  <th>Médecin</th>
                  <th>Heure</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {consultationData.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-gray-500">
                      Aucune consultation pour ce jour.
                    </td>
                  </tr>
                ) : (
                  consultationData.map(c => (
                    <tr key={c._id} className="border-t">
                      <td className="py-2">{c.patient_name || c.patient_id}</td>
                      <td>{c.doctor_name || c.doctor_id}</td>
                      <td>
                        {c.date_time ? new Date(c.date_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                      </td>
                      <td className="truncate max-w-xs">{c.notes || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-3">Progression du jour</h3>
          {loading ? <p className="text-sm">Chargement...</p> : (
            <ul className="space-y-2 text-sm">
              <li>Consultations réalisées : <b>{consultationData.length}</b></li>
              <li>Rendez-vous programmés : <b>{totalAppointments}</b></li>
              <li>Rendez-vous restants : <b>{pendingAppointments}</b></li>
              <li>Rendez-vous terminés : <b>{completedAppointments}</b></li>
              <li>Annulations : <b>{cancelledAppointments}</b></li>
            </ul>
          )}
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