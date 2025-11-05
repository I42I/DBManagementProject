import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

type Card = { title: string; desc: string; link: string; icon: string }

const cards: Card[] = [
  { title: 'Rendez-vous',  desc: 'Planifiez une consultation près de chez vous.', link: '/appointments', icon: '/images/icon-appointment.svg' },
  { title: 'Prescriptions', desc: 'Retrouvez vos ordonnances en ligne.',        link: '/services',     icon: '/images/icon-prescription.svg' },
  { title: 'Laboratoires',  desc: 'Consultez vos résultats d’analyse.',         link: '/results',      icon: '/images/icon-lab.svg' },
]

export default function Home() {
  return (
    <>
      {/* Hero */}
      <section className="bg-white" aria-labelledby="home-hero-title">
        <div className="container grid md:grid-cols-2 gap-10 items-center py-16">
          <div>
            <motion.h1
              id="home-hero-title"
              className="h1 mb-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              Votre santé, au cœur du Tchad
            </motion.h1>

            <p className="text-slate-700 mb-6">
              Un portail simple pour gérer vos rendez-vous, consulter vos résultats et
              communiquer avec les professionnels de santé — accessible, mobile et sécurisé.
            </p>

            <div className="flex gap-3">
              <Link to="/appointments" className="btn-primary">Prendre rendez-vous</Link>
              <Link to="/results" className="btn-outline">Consulter mes résultats</Link>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            aria-hidden="true"
          >
            <img
              src="/images/hero-illustration.svg"
              alt="Illustration d’un suivi de santé en ligne"
              className="w-full"
              loading="lazy"
            />
          </motion.div>
        </div>
      </section>

      {/* Services */}
      <section className="py-12" aria-labelledby="home-services-title">
        <div className="container">
          <h2 id="home-services-title" className="h2 mb-6">Services principaux</h2>

          <div className="grid md:grid-cols-3 gap-6">
            {cards.map((c) => (
              <motion.article
                key={c.title}
                className="card p-6"
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-20% 0px' }}
                transition={{ duration: 0.25 }}
                aria-labelledby={`card-${c.title}`}
              >
                <img
                  src={c.icon}
                  alt=""
                  className="h-12 mb-3"
                  loading="lazy"
                  aria-hidden="true"
                />
                <h3 id={`card-${c.title}`} className="font-semibold mb-1">
                  {c.title}
                </h3>
                <p className="text-sm text-slate-600 mb-4">{c.desc}</p>
                <Link to={c.link} className="text-primary font-medium">Accéder →</Link>
              </motion.article>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
