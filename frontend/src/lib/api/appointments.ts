import { http } from '../http'
import { scrub } from '../clean'

// ---- Types alignés sur ton backend ----

export type AppointmentStatus =
  | 'scheduled'
  | 'checked_in'
  | 'cancelled'
  | 'no_show'
  | 'completed'

// Document renvoyé par GET (liste/détail)
export type Appointment = {
  _id: string
  patient_id: string
  doctor_id: string
  facility_id: string
  date_time: string             // ISO (ex: "2025-10-31T10:00:00Z")
  status: AppointmentStatus
  reason?: string
  notes?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean

  // Champs enrichis par le back (pipeline $lookup)
  patient_name?: string
  patient_identifier?: string
}

// Corps attendu par POST /api/appointments
export type NewAppointment = {
  patient_id: string            // ObjectId (string)
  doctor_id: string             // ObjectId (string)
  facility_id?: string          // optionnel (généré côté back sinon)
  date_time: string             // ISO 8601 (avec 'Z' si UTC)
  status?: AppointmentStatus    // défaut "scheduled"
  reason?: string
  notes?: string
}

export type UpdateAppointment = Partial<NewAppointment>

// Aide: forcer un ISO avec 'Z' en UTC depuis Date ou string local
export function toISOZ(d: Date | string) {
  if (typeof d === 'string') {
    if (d.endsWith('Z')) return d
    const dt = new Date(d)
    const utc = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000)
    return utc.toISOString().replace(/\.\d{3}Z$/, 'Z')
  }
  const utc = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
  return utc.toISOString().replace(/\.\d{3}Z$/, 'Z')
}

// ---- Client HTTP ----

export const appointments = {
  /**
   * Liste avec filtres facultatifs:
   * - doctor_id / patient_id / facility_id
   * - status
   * - date_from / date_to (ISO 8601)
   * (le back limite à 200 et trie par date_time asc)
   */
  list: (params?: {
    doctor_id?: string
    patient_id?: string
    facility_id?: string
    status?: AppointmentStatus
    date_from?: string
    date_to?: string
  }) => {
    const qs = new URLSearchParams()
    if (params?.doctor_id) qs.set('doctor_id', params.doctor_id)
    if (params?.patient_id) qs.set('patient_id', params.patient_id)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    if (params?.status) qs.set('status', params.status as string)
    if (params?.date_from) qs.set('date_from', params.date_from)
    if (params?.date_to) qs.set('date_to', params.date_to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<Appointment[]>(`/api/appointments${suffix}`)
  },

  // Détail
  getById: (id: string) => http<Appointment>(`/api/appointments/${id}`),

  // Création simple (retourne { _id })
  create: (body: NewAppointment) =>
    http<{ _id: string }>(`/api/appointments`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Création -> refetch le détail
  createAndFetch: async (body: NewAppointment) => {
    const created = await http<{ _id: string }>(`/api/appointments`, {
      method: 'POST',
      body: JSON.stringify(scrub(body)),  // 👈 important
    })
    return appointments.getById(created._id)
  },

  // Mise à jour (PATCH)
  update: (id: string, body: UpdateAppointment) =>
    http<Appointment>(`/api/appointments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(scrub(body)),
    }),

  // Suppression (DELETE)
  delete: (id: string) =>
    http<void>(`/api/appointments/${id}`, {
      method: 'DELETE',
    }),

}
