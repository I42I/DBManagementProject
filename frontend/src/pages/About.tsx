import React from 'react'
import { Link } from 'react-router-dom'

export default function About() {
  return (
    <div className="container py-10">
      <h2 className="h2 mb-4">À propos</h2>

      <p className="text-slate-700 mb-6 max-w-3xl">
        CHAD Health facilite l’accès aux services de santé au Tchad pour les patients et les professionnels.
        Priorités&nbsp;: simplicité, sécurité et compatibilité mobile.
      </p>

      <div className="grid md:grid-cols-3 gap-6 mb-8" aria-label="Principes de la plateforme">
        <div className="card p-6">
          <h3 className="font-semibold">Simplicité</h3>
          <p className="text-sm text-slate-600 mt-2">
            Interface claire, responsive, pensée pour les réseaux contraints.
          </p>
        </div>
        <div className="card p-6">
          <h3 className="font-semibold">Sécurité</h3>
          <p className="text-sm text-slate-600 mt-2">
            Protection des données et confidentialité de bout en bout.
          </p>
        </div>
        <div className="card p-6">
          <h3 className="font-semibold">Accessibilité</h3>
          <p className="text-sm text-slate-600 mt-2">
            Tailles de police ajustables, contraste élevé, navigation clavier.
          </p>
        </div>
      </div>

      <div className="card p-6 flex items-center justify-between">
        <div>
          <h3 className="font-semibold mb-1">Une question&nbsp;?</h3>
          <p className="text-sm text-slate-600">Écris-nous et on te répond rapidement.</p>
        </div>
        <Link to="/contact" className="btn-primary">Contacter l’équipe</Link>
      </div>
    </div>
  )
}
