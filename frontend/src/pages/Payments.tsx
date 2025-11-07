import React, { useEffect, useState } from 'react'
import { payments, type Payment, type PayStatus } from '../lib/api/payments'

const STATUSES: PayStatus[] = ['pending', 'paid', 'failed', 'refunded', 'cancelled']

export default function PaymentsPage() {
    const [list, setList] = useState<Payment[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [status, setStatus] = useState<PayStatus | ''>('')

    useEffect(() => {
        ; (async () => {
            try {
                setLoading(true)
                setError(null)
                const data = await payments.list(status ? { status } : undefined)
                setList(data)
            } catch (e: any) {
                setError(e.message ?? 'Erreur de chargement')
            } finally {
                setLoading(false)
            }
        })()
    }, [status])

    return (
        <div className="container py-10 space-y-6">
            <header className="flex items-center justify-between">
                <h2 className="h2">Paiements</h2>
                <select
                    className="border rounded-xl px-3 py-2 text-sm"
                    value={status}
                    onChange={e => setStatus(e.target.value as PayStatus | '')}
                >
                    <option value="">Tous les statuts</option>
                    {STATUSES.map(s => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
            </header>

            {loading && <p>Chargement…</p>}
            {error && <p className="text-red-600 text-sm">{error}</p>}

            {!loading && !error && (
                <div className="card p-6 overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-left">
                                <th className="py-2">Patient</th>
                                <th>Montant</th>
                                <th>Devise</th>
                                <th>Méthode</th>
                                <th>Statut</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {list.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="py-6 text-center text-gray-500">
                                        Aucun paiement
                                    </td>
                                </tr>
                            ) : (
                                list.map(p => (
                                    <tr key={p._id} className="border-t">
                                        <td className="py-2">{p.patient_id}</td>
                                        <td>{p.amount.toFixed(0)}</td>
                                        <td>{p.currency}</td>
                                        <td>{p.method ?? '—'}</td>
                                        <td>{p.status}</td>
                                        <td>{p.created_at ? new Date(p.created_at).toLocaleString() : '—'}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}