import { http } from '../http'

export type ReportType = 'case_summary' | 'disease_reporting' | 'inventory' | 'other'
export type HAStatus   = 'draft' | 'submitted' | 'accepted' | 'rejected'

export type HAReport = {
  _id: string
  facility_id: string
  report_type: ReportType
  period_start: string
  period_end: string
  status: HAStatus
  payload?: Record<string, any>
  external_ref?: string
  notes?: string
  submitted_at?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

export type NewHAReport = {
  facility_id: string
  report_type: ReportType
  period_start: string
  period_end: string
  status: HAStatus
  payload?: Record<string, any>
  external_ref?: string
  notes?: string
  submitted_at?: string
}

export const healthAuthorities = {
  list: (params?: { facility_id?: string; report_type?: ReportType; status?: HAStatus }) => {
    const qs = new URLSearchParams()
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    if (params?.report_type) qs.set('report_type', params.report_type)
    if (params?.status) qs.set('status', params.status)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<HAReport[]>(`/api/health_authorities${suffix}`)
  },
  getById: (id: string) => http<HAReport>(`/api/health_authorities/${id}`),
  create: (body: NewHAReport) =>
    http<{ _id: string }>(`/api/health_authorities`, { method: 'POST', body: JSON.stringify(body) }),
}
