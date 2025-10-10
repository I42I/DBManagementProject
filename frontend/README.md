# Frontend - Plateforme de Digitalisation des Services Médicaux

## Description

Interface web minimaliste pour la gestion des services médicaux, permettant de consulter les patients, les consultations et l'historique médical.

## Structure

```
frontend/
├── index.html              # Page d'accueil
├── patients.html           # Liste des patients
├── consultations.html      # Consultations par docteur
├── patient-history.html    # Historique d'un patient
├── css/
│   └── styles.css         # Feuille de styles principale
└── js/
    └── app.js             # Logique JavaScript et données
```

## Pages

### 1. Page d'Accueil (index.html)
- Vue d'ensemble de la plateforme
- Cartes de fonctionnalités principales
- Navigation vers les différentes sections
- Description de l'objectif et des fonctionnalités clés

### 2. Liste des Patients (patients.html)
- Tableau complet des patients enregistrés
- Fonction de recherche (nom, condition, allergie)
- Affichage des informations importantes (allergies, conditions)
- Lien vers l'historique de chaque patient

### 3. Consultations par Docteur (consultations.html)
- Vue des consultations médicales
- Filtre par docteur
- Affichage des diagnostics et traitements
- Informations sur l'équipe médicale

### 4. Historique Patient (patient-history.html)
- Sélection d'un patient
- Informations détaillées du patient
- Chronologie des consultations et analyses
- Alertes et recommandations médicales

## Fonctionnalités

- **Responsive Design**: Interface adaptée aux mobiles et tablettes
- **Recherche et Filtres**: Recherche de patients et filtrage des consultations
- **Données Dynamiques**: Gestion des données via JavaScript
- **Navigation Intuitive**: Menu de navigation sur toutes les pages
- **Alertes Visuelles**: Badges pour allergies et conditions médicales

## Utilisation

Pour utiliser le frontend, ouvrez simplement `index.html` dans un navigateur web moderne:

```bash
# Avec un serveur HTTP local (recommandé)
cd frontend
python3 -m http.server 8000
# Ouvrir http://localhost:8000

# Ou directement dans le navigateur
open index.html
```

## Technologies

- **HTML5**: Structure des pages
- **CSS3**: Mise en forme et responsive design
- **JavaScript (Vanilla)**: Logique et interactivité
- **Aucune dépendance externe**: Pas de framework requis

## Données d'Exemple

Le fichier `app.js` contient des données d'exemple pour:
- 5 patients avec conditions médicales variées
- 4 docteurs avec différentes spécialités
- 5 consultations récentes
- Historique médical pour 3 patients

## Personnalisation

Pour ajouter de vraies données depuis une API backend:
1. Modifier les fonctions de chargement dans `app.js`
2. Remplacer les données statiques par des appels API (fetch)
3. Gérer les états de chargement et erreurs

## Notes

- Interface en français
- Conçu pour le contexte africain (références Mobile Money, etc.)
- Priorisation de la simplicité et de la clarté
- Pas de framework JavaScript lourd pour faciliter le déploiement

## Sécurité

⚠️ **Note importante**: Cette implémentation est un prototype/démo avec des données statiques. Pour une utilisation en production:
- Sanitiser toutes les entrées utilisateur pour prévenir les attaques XSS
- Implémenter une authentification et autorisation appropriées
- Utiliser HTTPS pour toutes les communications
- Valider et échapper les données côté serveur
- Implémenter une protection CSRF
- Gérer les données médicales conformément aux réglementations (RGPD, HIPAA, etc.)
