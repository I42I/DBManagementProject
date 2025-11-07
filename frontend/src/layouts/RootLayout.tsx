import React, { useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { Languages, Sun, Moon, Accessibility } from 'lucide-react'

export default function RootLayout() {
  const [dark, setDark] = useState(false)
  const [largeText, setLargeText] = useState(false)
  const [lang, setLang] = useState<'fr' | 'en' | 'ar'>('fr')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    document.documentElement.style.fontSize = largeText ? '18px' : '16px'
  }, [dark, largeText])

  return (
    <div className={dark ? 'dark bg-slate-900 text-slate-100' : ''}>
      <header className="border-b bg-white/70 backdrop-blur dark:bg-slate-900/60 sticky top-0 z-50">
        <div className="container py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 pr-6">
            <img src="/images/logo.svg" alt="Logo CHAD Health" className="h-9" />
            <span className="font-bold text-lg">CHAD Health</span>
          </Link>
          <nav className="hidden md:flex items-center gap-4 lg:gap-6 text-sm lg:text-base mx-6 px-4">
            <NavLink to="/" end className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Accueil</NavLink>
            <NavLink to="/services" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Services</NavLink>
            <NavLink to="/patients" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Patients</NavLink>
            <NavLink to="/professionals" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Professionnels</NavLink>
            <NavLink to="/payments" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Paiements</NavLink>
            <NavLink to="/notifications" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Notifications</NavLink>
            <NavLink to="/news" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Actualités</NavLink>
            <NavLink to="/about" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>À propos</NavLink>
            <NavLink to="/contact" className={({ isActive }) => isActive ? 'whitespace-nowrap text-primary font-semibold' : 'whitespace-nowrap hover:text-primary'}>Contact</NavLink>
          </nav>
          <div className="flex items-center gap-3 pl-6">
            <button aria-label="Contraste / mode sombre" className="btn btn-outline" onClick={() => setDark(v => !v)}>{dark ? <Sun size={18} /> : <Moon size={18} />}<span className="hidden md:inline">Contraste</span></button>
            <button aria-label="Accessibilité: texte large" className="btn btn-outline" onClick={() => setLargeText(v => !v)}><Accessibility size={18} /><span className="hidden md:inline">Texte</span></button>
            <button className="btn btn-outline"><Languages size={18} /><span className="hidden md:inline">Langue: {lang.toUpperCase()}</span></button>
          </div>
        </div>
      </header>
      <main><Outlet /></main>
      <footer className="mt-10 border-t">
        <div className="container py-8 grid md:grid-cols-4 gap-6">
          <div><div className="flex items-center gap-3 mb-3">
            <img src="/images/logo.svg" className="h-8" /><span className="font-bold">CHAD Health</span></div>
            <p className="text-sm text-slate-600">Plateforme de e-santé pour les citoyens et les professionnels au Tchad. Accès simplifié, sécurité des données, compatibilité mobile.</p>
          </div>
          <div><h4 className="font-semibold mb-2">Navigation</h4>
            <ul className="space-y-1 text-sm"><li><Link to="/">Accueil</Link></li><li><Link to="/services">Services</Link></li><li><Link to="/patients">Espace Patients</Link></li><li><Link to="/professionals">Espace Professionnels</Link></li></ul>
          </div>
          <div><h4 className="font-semibold mb-2">Légal</h4>
            <ul className="space-y-1 text-sm"><li><a>Confidentialité</a></li><li><a>Conditions</a></li><li><a>Cookies</a></li></ul>
          </div>
          <div><h4 className="font-semibold mb-2">Contact</h4>
            <p className="text-sm">N'Djamena, Tchad</p><p className="text-sm">contact@chadhealth.td</p>
          </div>
        </div>
        <div className="text-center text-xs text-slate-500 pb-6">© 2025 CHAD Health</div>
      </footer>
    </div>
  )
}