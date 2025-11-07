# 🏥 Hospital Management – NoSQL Backend

---

## Web App — Accès & vérification

- URL de test : https://chadhealth.msrl.be  
- Interface d'administration Mongo : https://mongo-chadhealth.msrl.be (mongo‑express)

## Docker Commands

This project is fully containerized for both production and development environments.

### Production Mode

The production setup runs the Flask backend and serves the frontend build from a single container.

To build and run the application in production mode:
```bash
docker-compose up --build -d
```
The application will be available at `http://localhost:5000`.

### Development Mode

The development setup uses a multi-container environment with hot-reloading for both the frontend and backend.

To run in development mode:
```bash
docker-compose -f docker-compose.dev.yml up --build -d
```
- The frontend (Vite) will be on `http://localhost:25173`.
- The backend (Flask) will be on `http://localhost:5000`.
- Mongo Express will be on `http://localhost:8081`.

---

## Overview

This project implements a **Flask-based backend** for a hospital digitalization platform.  
The goal is to centralize patient data, medical history, consultations, and prescriptions within a flexible **NoSQL database** (MongoDB).

The solution improves the reliability of medical records and reduces human errors (e.g., avoiding contraindicated medications).  
It is designed to be modular and scalable, allowing future extensions such as insurance, radiology, or emergency units.

---

## Features

- 👩‍⚕️ Manage patients, doctors, and facilities  
- 🗓️ Handle appointments and consultations  
- 💊 Generate and store prescriptions  
- 🧪 Record laboratory and test results  
- 💬 Notifications for reminders or follow-ups  
- 💰 Payments tracking  
- 🏢 Support for public health authorities and analytics  

All entities are stored as separate MongoDB collections and linked through document references.

---

## Architecture

The system follows a **modular, service-oriented design**:

Frontend (Web App)
↓ REST API
Flask Backend (app.py)
↓
MongoDB (hospital database)
↓
Mongo Express (Admin UI)

markdow```

### Tech Stack

| Layer | Technology |
|-------|-------------|
| **Backend** | Python Flask |
| **Database** | MongoDB |
| **Admin UI** | Mongo Express |
| **Cache** | Local cache logic in `__init__.py` |
| **Containerization** | Docker Compose |
| **Frontend** | Connected via REST API |

---

## Database Schema (Simplified)

| Collection | Description |
|-------------|-------------|
| **patients** | Identity, age, medical history, allergies |
| **doctors** | Name, specialty, facility |
| **appointments** | Link between patient & doctor, date, status |
| **consultations** | Diagnosis and associated prescriptions |
| **prescriptions** | Medicines with dosage and contraindications |
| **laboratories** | Test results linked to a patient |
| **notifications** | Alerts and reminders |
| **payments** | Record of fees and transactions |
| **facilities** | Hospital units or departments |
| **health_authorities** | Aggregated, anonymized data |

Example document structure:

```json
{
  "_id": "ObjectId('...')",
  "patient_id": "ObjectId('...')",
  "doctor_id": "ObjectId('...')",
  "date": "2025-11-05T14:00:00Z",
  "status": "confirmed"
}
```
---

# Installation & Setup

## Requirements
- Python 3.12+
- MongoDB (local or Docker)
- Mongo Express (optional for visualization)

## Start the backend:

```bash
python app.py
```

Backend will run on http://localhost:5000

Mongo Express interface: http://localhost:8081

Environment variables:

```bash
MONGO_URI=mongodb://localhost:27017
MONGO_DB=hospital
FLASK_DEBUG=1
```
---

## API Overview

| Endpoint             | Method                  | Description |
| -------------------- | ----------------------- | ------------ |
| `/api/patients`      | **GET / POST / PATCH / DELETE** | Retrieve all patients, add new record, update or delete a patient |
| `/api/doctors`       | **GET / POST / PATCH / DELETE** | Manage doctors and their information |
| `/api/appointments`  | **GET / POST / PATCH / DELETE** | Create, list, modify or cancel an appointment |
| `/api/consultations` | **GET / POST / PATCH / DELETE** | Record, update, or remove medical consultations |
| `/api/prescriptions` | **GET / POST / PATCH / DELETE** | Manage prescriptions and related medication data |
| `/api/notifications` | **GET / POST / PATCH / DELETE** | Create, send, update, or delete system notifications |

All responses are returned in **JSON** format.  
Each route includes basic validation and error handling to ensure data consistency within MongoDB.


---

## Scalability & Future Work

The backend is designed for horizontal scaling and schema flexibility:
- MongoDB allows dynamic document structures for evolving modules
- Flask is stateless, making deployment easy on multiple instances
- Caching logic (in __init__.py) improves performance for frequent reads

---

## Planned extensions

- Authentication and user roles
- Insurance and billing modules
- Analytics dashboard for hospital statistics
- Mobile app integration (SMS / USSD)
 
---

## Authors
- YAYA LIBIS Issakha (21252) 
- MASUREEL Bruno (23375)
- CHOKAYRI Omar (22379)

---

## Licence :

Academic project – ECAM Brussels (2025).

All data used for testing are fictitious.

