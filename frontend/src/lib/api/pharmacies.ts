import { http } from '../http'

export type PharmacyStatus = 'requested' | 'prepared' | 'dispensed' | 'cancelled'

export type PharmacyItem = {
  dci: string
  brand?: string
  forme?: string
  posologie?: string
  qty: number
  notes?: string
}

export type Pharmacy = {
  _id: string
  patient_id: string
  doctor_id: string
  prescription_id?: string
  facility_id: string
  status: PharmacyStatus
  items: PharmacyItem[]
  dispensed_at?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

export type NewPharmacy = {
  patient_id: string
  doctor_id: string
  prescription_id?: string
  facility_id?: string
  status: PharmacyStatus
  items: PharmacyItem[]
  dispensed_at?: string
  notes?: string
}

export const pharmacies = {
  list: (params?: { patient_id?: string; doctor_id?: string; facility_id?: string; status?: PharmacyStatus }) => {
    const qs = new URLSearchParams()
    if (params?.patient_id) qs.set('patient_id', params.patient_id)
    if (params?.doctor_id) qs.set('doctor_id', params.doctor_id)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    if (params?.status) qs.set('status', params.status)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<Pharmacy[]>(`/api/pharmacies${suffix}`)
  },
  getById: (id: string) => http<Pharmacy>(`/api/pharmacies/${id}`),
  create: (body: NewPharmacy) =>
    http<{ _id: string }>(`/api/pharmacies`, { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: Partial<NewPharmacy>) =>
    http<Pharmacy>(`/api/pharmacies/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (id: string) => http<void>(`/api/pharmacies/${id}`, { method: 'DELETE' }),
}
