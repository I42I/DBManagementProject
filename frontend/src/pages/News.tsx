import React from 'react'

type NewsItem = {
  title: string
  date: string
  excerpt: string
}

export default function News() {
  const items: NewsItem[] = [
    {
      title: 'Campagne de vaccination',
      date: '2025-10-05',
      excerpt: "Nouvelle campagne de vaccination à N'Djamena, organisée par le ministère de la Santé publique.",
    },
    {
      title: 'Nouveau laboratoire partenaire',
      date: '2025-09-18',
      excerpt: "Ouverture d'un centre d’analyses médicales moderne à Moundou, en partenariat avec CHAD Health.",
    },
  ]

  return (
    <div className="container py-10">
      <h2 className="h2 mb-6">Actualités</h2>

      {items.length === 0 ? (
        <p className="text-slate-600">Aucune actualité pour le moment.</p>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {items.map((n) => (
            <article
              key={n.title}
              className="card p-6 hover:shadow-lg transition-shadow"
              aria-labelledby={`news-${n.title}`}
            >
              <h3 id={`news-${n.title}`} className="font-semibold text-lg mb-1">
                {n.title}
              </h3>
              <p className="text-sm text-slate-500 mb-2">
                {new Date(n.date).toLocaleDateString('fr-FR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric',
                })}
              </p>
              <p className="text-sm text-slate-700 leading-relaxed">{n.excerpt}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
