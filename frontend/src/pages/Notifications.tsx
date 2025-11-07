import React, { useEffect, useState } from 'react'
import { notifications, type Notification, type NotifStatus } from '../lib/api/notifications'

const STATUSES: NotifStatus[] = ['queued', 'sent', 'failed', 'read']

export default function NotificationsPage() {
    const [list, setList] = useState<Notification[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [status, setStatus] = useState<NotifStatus | ''>('')

    useEffect(() => {
        ; (async () => {
            try {
                setLoading(true)
                setError(null)
                const data = await notifications.list(status ? { status } : undefined)
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
                <h2 className="h2">Notifications</h2>
                <select
                    className="border rounded-xl px-3 py-2 text-sm"
                    value={status}
                    onChange={e => setStatus(e.target.value as NotifStatus | '')}
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
                                <th className="py-2">Channel</th>
                                <th>Statut</th>
                                <th>Référence</th>
                                <th>Destinataire</th>
                                <th>Créée le</th>
                            </tr>
                        </thead>
                        <tbody>
                            {list.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="py-6 text-center text-gray-500">
                                        Aucune notification
                                    </td>
                                </tr>
                            ) : (
                                list.map(n => (
                                    <tr key={n._id} className="border-t">
                                        <td className="py-2">{n.channel}</td>
                                        <td>{n.status}</td>
                                        <td>{n.ref_type ? `${n.ref_type} · ${n.ref_id ?? '—'}` : '—'}</td>
                                        <td>{n.to_patient_id ?? n.to_doctor_id ?? '—'}</td>
                                        <td>{n.created_at ? new Date(n.created_at).toLocaleString() : '—'}</td>
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