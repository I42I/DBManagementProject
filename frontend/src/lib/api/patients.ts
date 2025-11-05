import { http } from '../http'
import { scrub } from '../clean'   // ✅ pour filtrer null/vides

// -------- Types alignés sur ton backend --------

export type PatientListItem = {
  _id: string
  identite: {
    prenom: string
    nom: string
    date_naissance?: string
    sexe?: 'M' | 'F' | 'X'
  }
  contacts?: { phone?: string }
  facility_id?: string // non projeté par /list, donc optionnel
  created_at?: string
  updated_at?: string
}

export type PatientFull = PatientListItem & {
  notes?: string
  allergies?: string[]
  chronic_diseases?: string[]
}

export type NewPatient = {
  facility_id?: string
  identite: {
    prenom: string
    nom: string
    date_naissance: string   // ISO ex: "2001-05-12T00:00:00Z"
    sexe: 'M' | 'F' | 'X'
  }
  contacts?: { phone?: string }
}

// -------- Helpers --------

export function patientLabel(p: PatientListItem | PatientFull) {
  const prenom = p.identite?.prenom ?? ''
  const nom    = p.identite?.nom ?? ''
  return `${prenom} ${nom}`.trim() || '—'
}

// Si tu veux forcer un ISO en Z depuis un Date
export function toISOZ(d: Date | string) {
  if (typeof d === 'string') return d.endsWith('Z') ? d : new Date(d).toISOString()
  return d.toISOString()
}

// -------- Client API --------

export const patients = {
  // Liste (ton backend ne gère pas de filtres pour l’instant)
  list: () => http<PatientListItem[]>('/api/patients'),

  // Détail
  getById: (id: string) => http<PatientFull>(`/api/patients/${id}`),

  // Création simple (avec nettoyage avant envoi)
  create: (body: NewPatient) =>
    http<{ _id: string }>('/api/patients', {
      method: 'POST',
      body: JSON.stringify(scrub(body)), // ✅ évite d’envoyer undefined/null
    }),

  // Création puis refetch du document complet
  createAndFetch: async (body: NewPatient) => {
    const created = await patients.create(body)
    return patients.getById(created._id)
  },

  update: (id: string, body: Partial<PatientFull>) =>
    http<PatientFull>(`/api/patients/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(scrub(body)),
    }),

  // Suppression (DELETE)
  delete: (id: string) =>
    http<void>(`/api/patients/${id}`, {
      method: 'DELETE',
    }),
}

