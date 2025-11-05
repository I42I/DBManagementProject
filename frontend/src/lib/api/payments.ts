import { http } from '../http'

export type Currency = 'XAF' | 'XOF' | 'EUR' | 'USD'
export type PayMethod = 'cash' | 'card' | 'mobile' | 'insurance'
export type PayStatus = 'pending' | 'paid' | 'failed' | 'refunded' | 'cancelled'
export type ItemRefType = 'appointment' | 'consultation' | 'laboratory' | 'pharmacy' | 'other'

export type PaymentItem = {
  ref_type?: ItemRefType
  label?: string
  amount?: number
  ref_id?: string
}

export type Payment = {
  _id: string
  patient_id: string
  appointment_id?: string
  consultation_id?: string
  facility_id: string
  invoice_no?: string
  amount: number
  currency: Currency
  method?: PayMethod
  status: PayStatus
  items?: PaymentItem[]
  due_date?: string
  paid_at?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

export type NewPayment = {
  patient_id: string
  appointment_id?: string
  consultation_id?: string
  facility_id?: string
  invoice_no?: string
  amount: number
  currency: Currency
  method?: PayMethod
  status: PayStatus
  items?: PaymentItem[]
  due_date?: string
  paid_at?: string
}

export const payments = {
  list: (params?: { patient_id?: string; facility_id?: string; status?: PayStatus; currency?: Currency; method?: PayMethod }) => {
    const qs = new URLSearchParams()
    if (params?.patient_id) qs.set('patient_id', params.patient_id)
    if (params?.facility_id) qs.set('facility_id', params.facility_id)
    if (params?.status) qs.set('status', params.status)
    if (params?.currency) qs.set('currency', params.currency)
    if (params?.method) qs.set('method', params.method)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<Payment[]>(`/api/payments${suffix}`)
  },
  getById: (id: string) => http<Payment>(`/api/payments/${id}`),
  create: (body: NewPayment) =>
    http<{ _id: string }>(`/api/payments`, { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: Partial<NewPayment>) =>
    http<Payment>(`/api/payments/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (id: string) => http<void>(`/api/payments/${id}`, { method: 'DELETE' }),
}
