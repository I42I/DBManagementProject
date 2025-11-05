import { http } from '../http'

// ===== Types alignés sur ton backend =====

export type DoctorListItem = {
  _id: string
  identite: {
    prenom: string
    nom: string
  }
  specialites: string[]
  facility_id?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

export type DoctorFull = DoctorListItem

export type NewDoctor = {
  facility_id?: string
  identite: {
    prenom: string
    nom: string
  }
  specialites: string[] // tableau non vide de strings non vides
}

// ===== Helpers =====

export function doctorLabel(d: DoctorListItem | DoctorFull) {
  const prenom = d.identite?.prenom ?? ''
  const nom    = d.identite?.nom ?? ''
  const spec   = d.specialites && d.specialites.length ? ` (${d.specialites[0]})` : ''
  return `${prenom} ${nom}${spec}`.trim()
}

// ===== Client =====

export const doctors = {
  // /api/doctors?specialite=Cardio&facility_id=...
  list: (params?: { specialite?: string; facility_id?: string }) => {
    const qs = new URLSearchParams()
    if (params?.specialite) qs.set('specialite', params.specialite)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<DoctorListItem[]>(`/api/doctors${suffix}`)
  },

  getById: (id: string) => http<DoctorFull>(`/api/doctors/${id}`),

  create: (body: NewDoctor) =>
    http<{ _id: string }>(`/api/doctors`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  createAndFetch: async (body: NewDoctor) => {
    const created = await doctors.create(body)
    return doctors.getById(created._id)
  },

  update: (id: string, body: Partial<DoctorFull>) =>
    http<DoctorFull>(`/api/doctors/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(scrub(body)),
    }),

  delete: (id: string) =>
    http<void>(`/api/doctors/${id}`, {
      method: 'DELETE',
    }),
}
