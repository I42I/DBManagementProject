import React, { Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import RootLayout from './layouts/RootLayout'
import Home from './pages/Home'
import Patients from './pages/Patients'
import Professionals from './pages/Professionals'
import Services from './pages/Services'
import News from './pages/News'
import About from './pages/About'
import Contact from './pages/Contact'
import Results from './pages/Results'
import Appointments from './pages/Appointments'
import Prescriptions from './pages/Prescriptions'
import PrescriptionDetail from './pages/PrescriptionDetail'   // ✅ import ajouté

import './index.css'

// --- Petites pages utilitaires ---
function NotFound() {
  return (
    <div style={{ padding: 24 }}>
      <h1 className="h2 mb-2">404</h1>
      <p>La page demandée n’existe pas.</p>
    </div>
  )
}

function RouteError() {
  return (
    <div style={{ padding: 24 }}>
      <h1 className="h2 mb-2">Oups…</h1>
      <p>Une erreur est survenue lors du chargement de cette page.</p>
    </div>
  )
}

// --- Définition du routeur principal ---
const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <RootLayout />,
      errorElement: <RouteError />, // erreurs de rendu de cette branche
      children: [
        { index: true, element: <Home /> },

        // Patients
        { path: 'patients', element: <Patients /> },

        // Professionnels (FR) + alias EN
        { path: 'professionnels', element: <Professionals /> },
        { path: 'professionals',  element: <Professionals /> },

        // Rendez-vous
        { path: 'appointments', element: <Appointments /> },
        // { path: 'rendez-vous', element: <Appointments /> }, // option FR

        // Autres pages
        { path: 'services', element: <Services /> },
        { path: 'results', element: <Results /> },
        { path: 'prescriptions', element: <Prescriptions /> },
        { path: 'prescriptions/:id', element: <PrescriptionDetail /> },  // ✅ ajout de la route dynamique
        { path: 'news', element: <News /> },
        { path: 'about', element: <About /> },
        { path: 'contact', element: <Contact /> },

        // 404 locale (pour toute sous-route inconnue sous '/')
        { path: '*', element: <NotFound /> },
      ],
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  }
)

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Suspense fallback={<div style={{ padding: 24 }}>Chargement…</div>}>
      <RouterProvider router={router} />
    </Suspense>
  </React.StrictMode>
)
