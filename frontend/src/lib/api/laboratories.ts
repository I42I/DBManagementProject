import { http } from '../http'

export type LabStatus = 'ordered' | 'in_progress' | 'completed' | 'cancelled'

export type LabTest = {
  code: string
  name: string
  status: string
  result?: string | number
  unit?: string
  ref_range?: string
  abnormal?: boolean
}

export type Laboratory = {
  _id: string
  patient_id: string
  doctor_id: string
  facility_id: string
  appointment_id?: string
  status: LabStatus
  date_ordered: string
  date_reported?: string
  tests?: LabTest[]
  notes?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

export type NewLaboratory = {
  patient_id: string
  doctor_id: string
  facility_id?: string
  appointment_id?: string
  status: LabStatus
  tests?: LabTest[]
  notes?: string
}

export const laboratories = {
  list: (params?: { patient_id?: string; doctor_id?: string; facility_id?: string; status?: LabStatus }) => {
    const qs = new URLSearchParams()
    if (params?.patient_id) qs.set('patient_id', params.patient_id)
    if (params?.doctor_id) qs.set('doctor_id', params.doctor_id)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    if (params?.status) qs.set('status', params.status)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<Laboratory[]>(`/api/laboratories${suffix}`)
  },
  getById: (id: string) => http<Laboratory>(`/api/laboratories/${id}`),
  create: (body: NewLaboratory) =>
    http<{ _id: string }>(`/api/laboratories`, { method: 'POST', body: JSON.stringify(body) }),
}
