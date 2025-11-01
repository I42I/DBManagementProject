import { http } from '../http'

export type Channel = 'sms' | 'email' | 'push'
export type NotifStatus = 'queued' | 'sent' | 'failed' | 'read'
export type RefType = 'appointment' | 'consultation' | 'prescription' | 'payment' | 'other'

export type Notification = {
  _id: string
  channel: Channel
  status: NotifStatus
  template?: string
  payload?: Record<string, any>
  ref_type?: RefType
  ref_id?: string
  to_patient_id?: string
  to_doctor_id?: string
  send_at?: string
  sent_at?: string
  expires_at?: string
  error?: string
  created_at?: string
  updated_at?: string
  deleted?: boolean
}

export type NewNotification = {
  channel: Channel
  status: NotifStatus
  template?: string
  payload?: Record<string, any>
  ref_type?: RefType
  ref_id?: string
  to_patient_id?: string
  to_doctor_id?: string
  send_at?: string
  sent_at?: string
  expires_at?: string
  error?: string
}

export const notifications = {
  list: (params?: { status?: NotifStatus; channel?: Channel; ref_type?: RefType; to_patient_id?: string; to_doctor_id?: string }) => {
    const qs = new URLSearchParams()
    if (params?.status) qs.set('status', params.status)
    if (params?.channel) qs.set('channel', params.channel)
    if (params?.ref_type) qs.set('ref_type', params.ref_type)
    if (params?.to_patient_id) qs.set('to_patient_id', params.to_patient_id)
    if (params?.to_doctor_id) qs.set('to_doctor_id', params.to_doctor_id)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return http<Notification[]>(`/api/notifications${suffix}`)
  },
  getById: (id: string) => http<Notification>(`/api/notifications/${id}`),
  create: (body: NewNotification) =>
    http<{ _id: string }>(`/api/notifications`, { method: 'POST', body: JSON.stringify(body) }),
}
