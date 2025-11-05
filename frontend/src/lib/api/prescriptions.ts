// src/lib/api/prescriptions.ts
import { http } from '../http'

// -------- Types alignés sur ton backend Flask --------

// Élément individuel dans une prescription
export type PrescriptionItem = {
  dci: string
  forme?: string
  posologie: string
  duree_j?: number
  contre_indications?: string
}

// Version légère (liste)
export type PrescriptionListItem = {
  _id: string
  patient_id: string
  doctor_id: string
  consultation_id: string
  facility_id?: string
  items: PrescriptionItem[]
  notes?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

// Version complète (pour /:id)
export type PrescriptionFull = PrescriptionListItem & {}

// Corps attendu pour POST /api/prescriptions
export type NewPrescription = {
  patient_id: string
  doctor_id: string
  consultation_id: string
  facility_id?: string
  items: PrescriptionItem[]
  notes?: string
  renouvellements?: number
}

// -------- Client API --------
export const prescriptions = {
  // Liste
  list: (params?: {
    patient_id?: string
    doctor_id?: string
    consultation_id?: string
    facility_id?: string
  }) => {
    const qs = new URLSearchParams()
    if (params?.patient_id) qs.set('patient_id', params.patient_id)
    if (params?.doctor_id) qs.set('doctor_id', params.doctor_id)
    if (params?.consultation_id) qs.set('consultation_id', params.consultation_id)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<PrescriptionListItem[]>(`/api/prescriptions${suffix}`)
  },

  // Détail
  getById: (id: string) => http<PrescriptionFull>(`/api/prescriptions/${id}`),

  // Création
  create: (body: NewPrescription) =>
    http<{ _id: string }>(`/api/prescriptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  // Création + refetch complet
  createAndFetch: async (body: NewPrescription) => {
    const created = await prescriptions.create(body)
    return prescriptions.getById(created._id)
  },

  // Mise à jour
  update: (id: string, body: Partial<NewPrescription>) =>
    http<PrescriptionFull>(`/api/prescriptions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  // Suppression
  delete: (id: string) => http<void>(`/api/prescriptions/${id}`, { method: 'DELETE' }),
}
