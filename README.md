# 🏥 Digitalization of Medical Services – NoSQL Mini Project

## Description

This project proposes a digital platform to centralize patients’ medical information and improve the quality of healthcare. The main goal is to prevent serious medical errors caused by missing history (for example, injecting glucose into a diabetic patient). The solution relies on a flexible NoSQL database, with modules for patients, doctors, prescriptions, pharmacies, and laboratories. It is designed to work even in low-connectivity environments thanks to offline mode and SMS/USSD integration.

## Entities

- **Patient**: Identity, medical history (allergies, chronic conditions such as diabetes).
- **Doctor**: Professional information, specialty, consultations.
- **Appointment**: Scheduling between patient and doctor.
- **Consultation**: Diagnosis, treatment, and related prescriptions.
- **Prescription**: List of prescribed medicines with alerts (e.g., contraindications for diabetics).
- **Pharmacy**: Verification and dispensing of prescriptions.
- **Laboratory**: Test results linked to the patient’s record.
- **Notification**: SMS reminders (medication intake, appointments).
- **Payment**: Management of medical fees (cash, Mobile Money).
- **Health Authority**: Aggregated anonymized data for statistics and public health monitoring.
