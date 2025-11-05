import React, { useState } from 'react'
import { http } from '../lib/http'

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', message: '' })
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.message) {
      setError('Veuillez remplir tous les champs.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      // appel backend simulé (POST /api/contacts)
      await http<{ ok: boolean }>('/api/contacts', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setSent(true)
    } catch (err: any) {
      console.error(err)
      setError('Échec de l’envoi. Vérifiez votre connexion.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container py-10">
      <h2 className="h2 mb-4">Contact</h2>
      <p className="text-slate-600 mb-6 max-w-2xl">
        Vous pouvez nous écrire pour toute question, suggestion ou demande de support technique.
      </p>

      <form onSubmit={submit} className="card p-6 max-w-xl">
        {!sent ? (
          <>
            <label className="block text-sm font-medium mb-1">Nom complet</label>
            <input
              name="name"
              className="border rounded-xl px-3 py-2 mb-3 w-full"
              value={form.name}
              onChange={handleChange}
              placeholder="Ex. : Amina D."
            />

            <label className="block text-sm font-medium mb-1">Adresse e-mail</label>
            <input
              name="email"
              type="email"
              className="border rounded-xl px-3 py-2 mb-3 w-full"
              value={form.email}
              onChange={handleChange}
              placeholder="Ex. : amina@example.com"
            />

            <label className="block text-sm font-medium mb-1">Message</label>
            <textarea
              name="message"
              className="border rounded-xl px-3 py-2 mb-4 w-full"
              rows={4}
              value={form.message}
              onChange={handleChange}
              placeholder="Décrivez votre demande ici..."
            />

            {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

            <button className="btn-primary" disabled={loading}>
              {loading ? 'Envoi en cours…' : 'Envoyer'}
            </button>
          </>
        ) : (
          <div className="text-center py-10">
            <h3 className="text-green-700 font-semibold mb-2">Message envoyé ✅</h3>
            <p className="text-slate-600 text-sm mb-4">
              Merci pour votre message. Notre équipe vous répondra dès que possible.
            </p>
            <button
              className="btn-outline"
              onClick={() => {
                setSent(false)
                setForm({ name: '', email: '', message: '' })
              }}
            >
              Envoyer un autre message
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
