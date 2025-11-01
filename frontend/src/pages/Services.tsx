import React from 'react'
import { Link } from 'react-router-dom'

export default function Services() {
  const services = [
    {
      title: 'Rendez-vous',
      text: 'Planifiez une consultation avec un médecin ou un spécialiste.',
      link: '/appointments',
      icon: '/images/icon-appointment.svg',
    },
    {
      title: 'Consultations',
      text: 'Accédez aux informations et comptes rendus médicaux.',
      link: '/professionals', // page pro (consultations)
      icon: '/images/icon-consultation.svg',
    },
    {
      title: 'Prescriptions',
      text: 'Visualisez vos ordonnances et traitements récents.',
      link: '/services', // à remplacer plus tard par /prescriptions
      icon: '/images/icon-prescription.svg',
    },
    {
      title: 'Laboratoires',
      text: 'Consultez les résultats d’analyses médicales en ligne.',
      link: '/results',
      icon: '/images/icon-lab.svg',
    },
    {
      title: 'Pharmacies',
      text: 'Trouvez les pharmacies partenaires et suivez vos délivrances.',
      link: '/services', // à remplacer plus tard par /pharmacies
      icon: '/images/icon-pharmacy.svg',
    },
    {
      title: 'Notifications',
      text: 'Recevez vos alertes médicales et rappels automatiques.',
      link: '/services', // futur module notifications
      icon: '/images/icon-notification.svg',
    },
  ]

  return (
    <div className="container py-10">
      <h2 className="h2 mb-6">Tous les services disponibles</h2>
      <p className="text-slate-600 mb-8 max-w-2xl">
        Retrouvez ici les principaux modules de la plateforme hospitalière :
        rendez-vous, consultations, laboratoires, ordonnances et plus encore.
      </p>

      <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
        {services.map((s) => (
          <div key={s.title} className="card p-6 flex flex-col items-start">
            <img src={s.icon} className="h-10 mb-3" alt={s.title} />
            <h3 className="font-semibold mb-1">{s.title}</h3>
            <p className="text-sm text-slate-600 mb-3 flex-1">{s.text}</p>
            <Link className="btn-outline mt-auto" to={s.link}>
              Accéder →
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}
