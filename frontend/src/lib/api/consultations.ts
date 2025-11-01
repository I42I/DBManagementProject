// src/lib/api/consultations.ts
import { http } from '../http'

// -------- Types alignés sur ton backend --------

// Liste allégée (utilisée par les modales, sélecteurs, etc.)
export type ConsultationListItem = {
  _id: string
  patient_id: string
  doctor_id: string
  facility_id?: string
  appointment_id?: string
  date_time?: string
  notes?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

// Consultation complète
export type ConsultationFull = ConsultationListItem & {
  symptomes?: any
  diagnostic?: any
  vital_signs?: any
  attachments?: any
}

// Corps attendu pour POST /api/consultations
export type NewConsultation = {
  patient_id: string
  doctor_id: string
  facility_id?: string
  appointment_id?: string
  date_time: string
  symptomes?: any
  diagnostic?: any
  notes?: any
  vital_signs?: any
  attachments?: any
}

/** Force un ISO UTC (suffixe Z) quel que soit le fuseau local */
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

// -------- Client API --------
export const consultations = {
  // Liste filtrable
  list: (params?: {
    patient_id?: string
    doctor_id?: string
    facility_id?: string
    date_from?: string
    date_to?: string
  }) => {
    const qs = new URLSearchParams()
    if (params?.patient_id) qs.set('patient_id', params.patient_id)
    if (params?.doctor_id) qs.set('doctor_id', params.doctor_id)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    if (params?.date_from) qs.set('date_from', params.date_from)
    if (params?.date_to) qs.set('date_to', params.date_to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<ConsultationListItem[]>(`/api/consultations${suffix}`)
  },

  // Détail
  getById: (id: string) => http<ConsultationFull>(`/api/consultations/${id}`),

  // Création simple
  create: (body: NewConsultation) =>
    http<{ _id: string }>(`/api/consultations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  // Création + refetch complet
  createAndFetch: async (body: NewConsultation) => {
    const created = await consultations.create(body)
    return consultations.getById(created._id)
  },
}
