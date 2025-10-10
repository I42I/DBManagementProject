# Database Schema Documentation

## NoSQL Database Design for Medical Services Platform

### Database Technology: MongoDB

MongoDB was chosen for this project due to its:
- Document-oriented structure (natural fit for medical records)
- Flexible schema (healthcare data evolves frequently)
- Horizontal scalability
- Strong consistency with replica sets
- Excellent aggregation framework for analytics
- Good offline synchronization support

---

## Collections Overview

| Collection | Purpose | Estimated Size (Year 1) |
|------------|---------|-------------------------|
| patients | Patient demographics and medical history | 100,000 documents |
| doctors | Healthcare provider information | 500 documents |
| consultations | Medical consultation records | 500,000 documents |
| prescriptions | Digital prescriptions | 450,000 documents |
| appointments | Scheduled appointments | 200,000 documents |
| laboratories | Lab test orders and results | 300,000 documents |
| notifications | Alerts and reminders | 1,000,000 documents |
| payments | Payment transactions | 500,000 documents |
| pharmacies | Pharmacy information | 200 documents |
| medications | Drug database | 5,000 documents |
| audit_logs | System audit trail | 5,000,000 documents |
| health_stats | Anonymized statistics | 50,000 documents |

---

## Detailed Schema Definitions

### 1. Patients Collection

```javascript
// Collection: patients
{
  "_id": "PAT-001",  // Auto-generated or custom ID
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "middle_name": "Michael",
    "date_of_birth": ISODate("1985-06-15"),
    "gender": "M",  // M, F, Other
    "national_id": "CM-1234567",
    "phone": "+237670123456",
    "email": "john.doe@example.com",
    "address": {
      "street": "123 Main Street",
      "city": "Douala",
      "region": "Littoral",
      "country": "Cameroon",
      "postal_code": "1234"
    },
    "photo_url": "https://storage.example.com/patients/PAT-001.jpg"
  },
  "medical_history": {
    "blood_type": "O+",
    "allergies": [
      {
        "allergen": "Penicillin",
        "severity": "severe",  // mild, moderate, severe
        "reaction": "Anaphylaxis",
        "date_identified": ISODate("2010-03-15")
      },
      {
        "allergen": "Peanuts",
        "severity": "moderate",
        "reaction": "Hives and swelling",
        "date_identified": ISODate("2015-07-20")
      }
    ],
    "chronic_conditions": [
      {
        "condition": "Type 2 Diabetes",
        "diagnosed_date": ISODate("2018-05-10"),
        "status": "active",  // active, managed, resolved
        "notes": "Controlled with medication and diet"
      },
      {
        "condition": "Hypertension",
        "diagnosed_date": ISODate("2019-02-20"),
        "status": "active",
        "notes": "Stage 1 hypertension"
      }
    ],
    "immunizations": [
      {
        "vaccine": "COVID-19",
        "date": ISODate("2021-06-15"),
        "dose_number": 2,
        "manufacturer": "Pfizer"
      }
    ],
    "surgeries": [
      {
        "procedure": "Appendectomy",
        "date": ISODate("2015-08-10"),
        "hospital": "Central Hospital",
        "surgeon": "Dr. Smith"
      }
    ],
    "family_history": [
      {
        "relation": "Father",
        "condition": "Heart Disease",
        "age_at_diagnosis": 55
      }
    ]
  },
  "emergency_contact": {
    "name": "Jane Doe",
    "relationship": "Spouse",
    "phone": "+237670999888",
    "email": "jane.doe@example.com"
  },
  "insurance": {
    "provider": "National Health Insurance",
    "policy_number": "INS-123456",
    "expiry_date": ISODate("2025-12-31"),
    "coverage_type": "comprehensive"
  },
  "preferences": {
    "language": "en",  // en, fr
    "notification_method": "sms",  // sms, email, both
    "privacy_settings": {
      "share_with_researchers": false,
      "share_with_health_authority": true
    }
  },
  "status": "active",  // active, inactive, deceased
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "updated_at": ISODate("2024-03-20T14:30:00Z"),
  "created_by": "ADMIN-001",
  "updated_by": "DOC-001"
}

// Indexes
db.patients.createIndex({ "personal_info.national_id": 1 }, { unique: true });
db.patients.createIndex({ "personal_info.phone": 1 });
db.patients.createIndex({ "personal_info.email": 1 });
db.patients.createIndex({ "personal_info.last_name": 1, "personal_info.first_name": 1 });
db.patients.createIndex({ "status": 1 });
db.patients.createIndex({ "created_at": -1 });
```

### 2. Doctors Collection

```javascript
// Collection: doctors
{
  "_id": "DOC-001",
  "personal_info": {
    "title": "Dr.",
    "first_name": "Sarah",
    "last_name": "Smith",
    "date_of_birth": ISODate("1980-03-12"),
    "gender": "F",
    "phone": "+237670555666",
    "email": "dr.smith@hospital.cm",
    "photo_url": "https://storage.example.com/doctors/DOC-001.jpg"
  },
  "professional_info": {
    "license_number": "MED-12345",
    "license_expiry": ISODate("2026-12-31"),
    "specialty": "Cardiology",
    "sub_specialties": ["Interventional Cardiology"],
    "qualifications": [
      {
        "degree": "MD",
        "institution": "University of Yaoundé",
        "year": 2005
      },
      {
        "degree": "Fellowship in Cardiology",
        "institution": "Johns Hopkins Hospital",
        "year": 2010
      }
    ],
    "years_of_experience": 15,
    "languages": ["English", "French"],
    "certifications": [
      {
        "name": "Board Certified Cardiologist",
        "issuer": "Medical Council",
        "issue_date": ISODate("2010-06-15"),
        "expiry_date": ISODate("2030-06-15")
      }
    ]
  },
  "employment": {
    "hospital_id": "HOSP-001",
    "hospital_name": "Central Hospital",
    "department": "Cardiology",
    "position": "Senior Consultant",
    "employment_type": "full-time",  // full-time, part-time, consultant
    "start_date": ISODate("2015-01-01")
  },
  "schedule": {
    "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "working_hours": {
      "start": "08:00",
      "end": "17:00",
      "lunch_break": {
        "start": "12:00",
        "end": "13:00"
      }
    },
    "consultation_duration": 30,  // minutes
    "max_patients_per_day": 16
  },
  "fees": {
    "consultation_fee": 10000,  // XAF
    "follow_up_fee": 7500,
    "emergency_fee": 15000,
    "currency": "XAF"
  },
  "rating": {
    "average_rating": 4.7,
    "total_reviews": 156,
    "total_consultations": 5230
  },
  "status": "active",  // active, on-leave, inactive
  "created_at": ISODate("2024-01-01T08:00:00Z"),
  "updated_at": ISODate("2024-03-15T10:00:00Z")
}

// Indexes
db.doctors.createIndex({ "professional_info.license_number": 1 }, { unique: true });
db.doctors.createIndex({ "professional_info.specialty": 1 });
db.doctors.createIndex({ "employment.hospital_id": 1 });
db.doctors.createIndex({ "personal_info.email": 1 });
db.doctors.createIndex({ "status": 1 });
```

### 3. Consultations Collection

```javascript
// Collection: consultations
{
  "_id": "CONS-001",
  "patient_id": "PAT-001",
  "doctor_id": "DOC-001",
  "appointment_id": "APT-001",  // Reference to appointment if booked
  "consultation_date": ISODate("2024-03-20T14:30:00Z"),
  "type": "follow-up",  // initial, follow-up, emergency, routine
  "chief_complaint": "Chest pain and shortness of breath",
  "symptoms": [
    {
      "name": "chest pain",
      "severity": "moderate",  // mild, moderate, severe
      "duration": "2 days",
      "description": "Sharp pain in center of chest"
    },
    {
      "name": "shortness of breath",
      "severity": "mild",
      "duration": "1 day",
      "description": "Difficulty breathing after climbing stairs"
    }
  ],
  "vital_signs": {
    "blood_pressure": {
      "systolic": 140,
      "diastolic": 90,
      "unit": "mmHg"
    },
    "heart_rate": 88,
    "temperature": {
      "value": 37.2,
      "unit": "celsius"
    },
    "respiratory_rate": 18,
    "oxygen_saturation": 97,
    "weight": {
      "value": 85,
      "unit": "kg"
    },
    "height": {
      "value": 175,
      "unit": "cm"
    },
    "bmi": 27.8
  },
  "physical_examination": {
    "general": "Alert and oriented, mild distress",
    "cardiovascular": "Regular rhythm, no murmurs",
    "respiratory": "Clear bilateral breath sounds",
    "abdomen": "Soft, non-tender",
    "neurological": "Normal"
  },
  "diagnosis": {
    "primary": {
      "code": "I25.10",  // ICD-10 code
      "description": "Atherosclerotic heart disease",
      "type": "confirmed"  // suspected, confirmed, rule-out
    },
    "secondary": [
      {
        "code": "E11.9",
        "description": "Type 2 diabetes mellitus",
        "type": "confirmed"
      }
    ]
  },
  "treatment_plan": {
    "medications": ["Refer to prescription PRES-001"],
    "procedures": [
      {
        "name": "ECG",
        "status": "ordered",
        "urgency": "routine"
      }
    ],
    "lifestyle_modifications": [
      "Low-sodium diet",
      "Regular exercise 30 min/day",
      "Stress management"
    ],
    "follow_up": {
      "recommended_date": ISODate("2024-04-20T14:30:00Z"),
      "reason": "Review ECG results and medication effectiveness"
    }
  },
  "lab_orders": ["LAB-001", "LAB-002"],
  "prescription_id": "PRES-001",
  "referrals": [
    {
      "referred_to": "DOC-015",  // Cardiologist
      "specialty": "Cardiology",
      "reason": "Detailed cardiac evaluation",
      "urgency": "routine"
    }
  ],
  "notes": "Patient advised to monitor blood pressure daily. Discussed diabetes management and cardiac risk factors.",
  "attachments": [
    {
      "type": "image",
      "url": "https://storage.example.com/consultations/CONS-001-ecg.jpg",
      "description": "ECG reading",
      "uploaded_at": ISODate("2024-03-20T15:00:00Z")
    }
  ],
  "duration_minutes": 30,
  "status": "completed",  // scheduled, in-progress, completed, cancelled
  "created_at": ISODate("2024-03-20T14:30:00Z"),
  "updated_at": ISODate("2024-03-20T15:00:00Z")
}

// Indexes
db.consultations.createIndex({ "patient_id": 1, "consultation_date": -1 });
db.consultations.createIndex({ "doctor_id": 1, "consultation_date": -1 });
db.consultations.createIndex({ "appointment_id": 1 });
db.consultations.createIndex({ "consultation_date": -1 });
db.consultations.createIndex({ "status": 1 });
```

### 4. Prescriptions Collection

```javascript
// Collection: prescriptions
{
  "_id": "PRES-001",
  "consultation_id": "CONS-001",
  "patient_id": "PAT-001",
  "doctor_id": "DOC-001",
  "date_issued": ISODate("2024-03-20T15:00:00Z"),
  "valid_until": ISODate("2024-04-20T15:00:00Z"),
  "medications": [
    {
      "medication_id": "MED-001",
      "name": "Metformin",
      "generic_name": "Metformin Hydrochloride",
      "dosage": "500mg",
      "form": "tablet",  // tablet, capsule, syrup, injection, cream
      "route": "oral",  // oral, topical, injection, inhalation
      "frequency": "twice daily",
      "frequency_code": "BID",  // QD, BID, TID, QID
      "duration": "30 days",
      "quantity": 60,
      "instructions": "Take with meals. Monitor blood sugar levels.",
      "refills_allowed": 2,
      "refills_remaining": 2,
      "contraindications_checked": true,
      "allergy_checked": true,
      "interaction_checked": true,
      "warnings": [
        "Monitor kidney function",
        "May cause gastrointestinal upset"
      ]
    },
    {
      "medication_id": "MED-015",
      "name": "Aspirin",
      "generic_name": "Acetylsalicylic Acid",
      "dosage": "81mg",
      "form": "tablet",
      "route": "oral",
      "frequency": "once daily",
      "frequency_code": "QD",
      "duration": "ongoing",
      "quantity": 30,
      "instructions": "Take in the morning after breakfast.",
      "refills_allowed": 5,
      "refills_remaining": 5,
      "contraindications_checked": true,
      "allergy_checked": true,
      "interaction_checked": true,
      "warnings": [
        "Avoid if bleeding disorder",
        "Take with food to reduce stomach upset"
      ]
    }
  ],
  "safety_checks": {
    "allergy_check": {
      "performed": true,
      "timestamp": ISODate("2024-03-20T15:00:00Z"),
      "result": "passed",  // passed, warning, failed
      "alerts": []
    },
    "drug_interaction_check": {
      "performed": true,
      "timestamp": ISODate("2024-03-20T15:00:00Z"),
      "result": "passed",
      "interactions": []
    },
    "contraindication_check": {
      "performed": true,
      "timestamp": ISODate("2024-03-20T15:00:00Z"),
      "result": "warning",
      "alerts": [
        {
          "level": "warning",
          "message": "Patient has diabetes - monitor blood sugar closely with Metformin"
        }
      ]
    },
    "pregnancy_check": {
      "performed": true,
      "result": "not_applicable"
    }
  },
  "special_instructions": "Take Metformin with meals to reduce gastrointestinal side effects. Monitor blood sugar levels daily.",
  "diagnosis_codes": ["E11.9", "I25.10"],
  "pharmacy_id": null,  // Set when dispensed
  "dispensed_by": null,
  "dispensed_date": null,
  "status": "pending",  // pending, dispensed, cancelled, expired
  "digital_signature": {
    "doctor_id": "DOC-001",
    "signed_at": ISODate("2024-03-20T15:00:00Z"),
    "signature_hash": "abc123..."
  },
  "created_at": ISODate("2024-03-20T15:00:00Z"),
  "updated_at": ISODate("2024-03-20T15:00:00Z")
}

// Indexes
db.prescriptions.createIndex({ "patient_id": 1, "date_issued": -1 });
db.prescriptions.createIndex({ "doctor_id": 1, "date_issued": -1 });
db.prescriptions.createIndex({ "consultation_id": 1 });
db.prescriptions.createIndex({ "status": 1 });
db.prescriptions.createIndex({ "valid_until": 1 });
```

### 5. Appointments Collection

```javascript
// Collection: appointments
{
  "_id": "APT-001",
  "patient_id": "PAT-001",
  "doctor_id": "DOC-001",
  "scheduled_date": ISODate("2024-03-20T14:30:00Z"),
  "end_time": ISODate("2024-03-20T15:00:00Z"),
  "type": "follow-up",  // initial, follow-up, emergency, check-up
  "reason": "Diabetes follow-up consultation",
  "notes": "Patient requested appointment for medication review",
  "status": "completed",  // scheduled, confirmed, in-progress, completed, cancelled, no-show
  "confirmation": {
    "confirmed": true,
    "confirmed_at": ISODate("2024-03-19T10:00:00Z"),
    "confirmed_by": "sms"  // phone, sms, email, app
  },
  "reminders": [
    {
      "type": "sms",
      "scheduled_for": ISODate("2024-03-19T14:30:00Z"),  // 24h before
      "sent": true,
      "sent_at": ISODate("2024-03-19T14:30:15Z")
    },
    {
      "type": "sms",
      "scheduled_for": ISODate("2024-03-20T12:30:00Z"),  // 2h before
      "sent": true,
      "sent_at": ISODate("2024-03-20T12:30:10Z")
    }
  ],
  "check_in": {
    "checked_in": true,
    "checked_in_at": ISODate("2024-03-20T14:15:00Z"),
    "checked_in_by": "RECEP-001"
  },
  "cancellation": {
    "cancelled": false,
    "cancelled_at": null,
    "cancelled_by": null,
    "reason": null
  },
  "consultation_id": "CONS-001",  // Linked after consultation
  "created_at": ISODate("2024-03-15T10:00:00Z"),
  "created_by": "PAT-001",  // or staff member ID
  "updated_at": ISODate("2024-03-20T15:00:00Z")
}

// Indexes
db.appointments.createIndex({ "patient_id": 1, "scheduled_date": -1 });
db.appointments.createIndex({ "doctor_id": 1, "scheduled_date": 1 });
db.appointments.createIndex({ "scheduled_date": 1, "status": 1 });
db.appointments.createIndex({ "status": 1 });
```

### 6. Laboratories Collection

```javascript
// Collection: laboratories
{
  "_id": "LAB-001",
  "patient_id": "PAT-001",
  "consultation_id": "CONS-001",
  "ordered_by": "DOC-001",
  "order_date": ISODate("2024-03-20T15:30:00Z"),
  "test_type": "Blood Glucose",
  "test_code": "GLU",  // LOINC code
  "category": "blood_chemistry",  // blood_chemistry, hematology, microbiology, etc.
  "priority": "routine",  // routine, urgent, stat
  "clinical_notes": "Monitor diabetes control",
  "specimen": {
    "type": "blood",  // blood, urine, tissue, swab
    "collection_date": ISODate("2024-03-21T08:00:00Z"),
    "collected_by": "NURSE-001",
    "volume": "5ml"
  },
  "results": {
    "value": 180,
    "unit": "mg/dL",
    "reference_range": {
      "min": 70,
      "max": 100,
      "unit": "mg/dL"
    },
    "status": "elevated",  // normal, elevated, decreased, critical
    "interpretation": "Fasting glucose elevated - indicates poor diabetes control",
    "critical_value": false,
    "result_date": ISODate("2024-03-21T09:00:00Z"),
    "verified_by": "LABTECH-001",
    "verified_at": ISODate("2024-03-21T09:15:00Z")
  },
  "report": {
    "report_url": "https://storage.example.com/labs/LAB-001-report.pdf",
    "generated_at": ISODate("2024-03-21T09:20:00Z")
  },
  "notification": {
    "doctor_notified": true,
    "notified_at": ISODate("2024-03-21T09:20:00Z"),
    "patient_notified": true,
    "patient_notified_at": ISODate("2024-03-21T10:00:00Z")
  },
  "status": "completed",  // ordered, collected, in-progress, completed, cancelled
  "created_at": ISODate("2024-03-20T15:30:00Z"),
  "updated_at": ISODate("2024-03-21T09:20:00Z")
}

// Indexes
db.laboratories.createIndex({ "patient_id": 1, "order_date": -1 });
db.laboratories.createIndex({ "ordered_by": 1, "order_date": -1 });
db.laboratories.createIndex({ "consultation_id": 1 });
db.laboratories.createIndex({ "status": 1 });
db.laboratories.createIndex({ "results.status": 1 });
```

### 7. Notifications Collection

```javascript
// Collection: notifications
{
  "_id": "NOT-001",
  "recipient_id": "PAT-001",
  "recipient_type": "patient",  // patient, doctor, pharmacist, admin
  "type": "medication_reminder",  // appointment, medication, lab_result, general
  "priority": "normal",  // low, normal, high, urgent
  "title": "Medication Reminder",
  "message": "Time to take your Metformin medication (500mg)",
  "channel": "sms",  // sms, email, push, ussd
  "scheduled_time": ISODate("2024-03-21T08:00:00Z"),
  "sent": true,
  "sent_time": ISODate("2024-03-21T08:00:15Z"),
  "delivery_status": "delivered",  // pending, sent, delivered, failed
  "read": false,
  "read_at": null,
  "related_entities": {
    "prescription_id": "PRES-001",
    "medication_name": "Metformin"
  },
  "metadata": {
    "sms_id": "SMS-123456",
    "provider": "AfricasTalking",
    "cost": 25  // XAF
  },
  "retry_count": 0,
  "created_at": ISODate("2024-03-20T15:00:00Z"),
  "updated_at": ISODate("2024-03-21T08:00:15Z")
}

// Indexes
db.notifications.createIndex({ "recipient_id": 1, "scheduled_time": -1 });
db.notifications.createIndex({ "scheduled_time": 1, "sent": 1 });
db.notifications.createIndex({ "type": 1, "scheduled_time": -1 });
db.notifications.createIndex({ "delivery_status": 1 });
```

### 8. Payments Collection

```javascript
// Collection: payments
{
  "_id": "PAY-001",
  "patient_id": "PAT-001",
  "consultation_id": "CONS-001",
  "appointment_id": "APT-001",
  "invoice_number": "INV-2024-001",
  "amount": 10000,
  "currency": "XAF",
  "payment_method": "mobile_money",  // cash, mobile_money, credit_card, insurance
  "payment_details": {
    "provider": "MTN Mobile Money",
    "phone_number": "+237670123456",
    "transaction_id": "MM-12345678",
    "reference_number": "REF-2024-001"
  },
  "status": "completed",  // pending, processing, completed, failed, refunded
  "payment_date": ISODate("2024-03-20T15:45:00Z"),
  "description": "Consultation fee - Dr. Sarah Smith",
  "breakdown": [
    {
      "item": "Consultation Fee",
      "amount": 10000,
      "currency": "XAF"
    }
  ],
  "receipt": {
    "receipt_number": "REC-2024-001",
    "receipt_url": "https://storage.example.com/receipts/PAY-001.pdf",
    "generated_at": ISODate("2024-03-20T15:46:00Z")
  },
  "refund": {
    "refunded": false,
    "refund_amount": null,
    "refund_date": null,
    "refund_reason": null
  },
  "created_at": ISODate("2024-03-20T15:45:00Z"),
  "updated_at": ISODate("2024-03-20T15:46:00Z")
}

// Indexes
db.payments.createIndex({ "patient_id": 1, "payment_date": -1 });
db.payments.createIndex({ "consultation_id": 1 });
db.payments.createIndex({ "invoice_number": 1 }, { unique: true });
db.payments.createIndex({ "status": 1 });
db.payments.createIndex({ "payment_date": -1 });
```

### 9. Medications Collection (Reference Data)

```javascript
// Collection: medications
{
  "_id": "MED-001",
  "name": "Metformin",
  "generic_name": "Metformin Hydrochloride",
  "brand_names": ["Glucophage", "Fortamet"],
  "drug_class": "Biguanides",
  "forms": ["tablet", "extended-release tablet"],
  "strengths": ["500mg", "850mg", "1000mg"],
  "routes": ["oral"],
  "indications": ["Type 2 Diabetes Mellitus"],
  "contraindications": [
    "Renal impairment",
    "Metabolic acidosis",
    "Hypoxic states"
  ],
  "warnings": [
    "Risk of lactic acidosis",
    "Monitor kidney function",
    "May cause vitamin B12 deficiency"
  ],
  "side_effects": [
    {
      "effect": "Nausea",
      "frequency": "common"
    },
    {
      "effect": "Diarrhea",
      "frequency": "common"
    }
  ],
  "interactions": [
    {
      "drug": "Alcohol",
      "severity": "moderate",
      "description": "Increases risk of lactic acidosis"
    }
  ],
  "pregnancy_category": "B",
  "storage": "Store at room temperature",
  "manufacturer": "Multiple",
  "status": "active",
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-01-01T00:00:00Z")
}

// Indexes
db.medications.createIndex({ "name": 1 });
db.medications.createIndex({ "generic_name": 1 });
db.medications.createIndex({ "drug_class": 1 });
```

### 10. Audit Logs Collection

```javascript
// Collection: audit_logs
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2024-03-20T14:30:00Z"),
  "user_id": "DOC-001",
  "user_type": "doctor",
  "action": "VIEW_PATIENT_RECORD",
  "resource_type": "patient",
  "resource_id": "PAT-001",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "session_id": "SESSION-123456",
  "result": "success",  // success, failure, error
  "details": {
    "accessed_sections": ["medical_history", "allergies", "chronic_conditions"],
    "reason": "Emergency consultation"
  },
  "changes": null,  // For UPDATE actions, store before/after
  "created_at": ISODate("2024-03-20T14:30:00Z")
}

// Indexes
db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "resource_id": 1, "action": 1 });
db.audit_logs.createIndex({ "action": 1, "timestamp": -1 });
// TTL Index - automatically delete logs older than 2 years
db.audit_logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 63072000 });
```

---

## Data Relationships

### Relationship Patterns

1. **Reference Pattern** (Most Common)
   - Used for: Patient → Consultations, Doctor → Consultations
   - Implementation: Store IDs and use $lookup for joins
   - Benefit: Reduces data duplication, maintains data integrity

2. **Embedded Pattern**
   - Used for: Allergies in Patient, Medications in Prescription
   - Implementation: Nest documents within parent
   - Benefit: Faster reads, atomic updates

3. **Hybrid Pattern**
   - Used for: Patient summary in Consultation (embed), Full patient (reference)
   - Implementation: Embed frequently accessed data, reference complete document
   - Benefit: Balance between performance and data consistency

### Common Queries and Aggregations

```javascript
// 1. Get patient's complete medical history
db.patients.aggregate([
  { $match: { _id: "PAT-001" } },
  { $lookup: {
      from: "consultations",
      localField: "_id",
      foreignField: "patient_id",
      as: "consultations"
  }},
  { $lookup: {
      from: "prescriptions",
      localField: "_id",
      foreignField: "patient_id",
      as: "prescriptions"
  }},
  { $lookup: {
      from: "laboratories",
      localField: "_id",
      foreignField: "patient_id",
      as: "lab_results"
  }}
]);

// 2. Find all appointments for today
db.appointments.find({
  scheduled_date: {
    $gte: ISODate("2024-03-20T00:00:00Z"),
    $lt: ISODate("2024-03-21T00:00:00Z")
  },
  status: "scheduled"
}).sort({ scheduled_date: 1 });

// 3. Get pending prescriptions for pharmacy
db.prescriptions.find({
  status: "pending",
  valid_until: { $gte: new Date() }
}).sort({ date_issued: -1 });

// 4. Disease surveillance - count diagnoses by type
db.consultations.aggregate([
  { $match: {
      consultation_date: {
        $gte: ISODate("2024-03-01"),
        $lt: ISODate("2024-04-01")
      }
  }},
  { $group: {
      _id: "$diagnosis.primary.description",
      count: { $sum: 1 }
  }},
  { $sort: { count: -1 } },
  { $limit: 10 }
]);

// 5. Find patients with specific allergies
db.patients.find({
  "medical_history.allergies.allergen": "Penicillin"
}, {
  "personal_info.first_name": 1,
  "personal_info.last_name": 1,
  "personal_info.phone": 1,
  "medical_history.allergies": 1
});
```

---

## Data Validation

MongoDB schema validation rules can be applied to ensure data quality:

```javascript
db.createCollection("patients", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["personal_info", "medical_history", "status"],
      properties: {
        personal_info: {
          bsonType: "object",
          required: ["first_name", "last_name", "date_of_birth", "gender", "national_id", "phone"],
          properties: {
            gender: {
              enum: ["M", "F", "Other"]
            },
            phone: {
              bsonType: "string",
              pattern: "^\\+[0-9]{10,15}$"
            }
          }
        },
        status: {
          enum: ["active", "inactive", "deceased"]
        }
      }
    }
  }
});
```

---

## Backup and Recovery Strategy

### Backup Schedule
- **Full Backup**: Daily at 2:00 AM
- **Incremental Backup**: Every 6 hours
- **Retention**: 30 days

### Recovery Procedures
1. Point-in-time recovery from incremental backups
2. Full restore from daily backups
3. Replica set automatic failover for high availability

---

## Conclusion

This database schema provides a comprehensive foundation for the medical services platform with:
- Flexible document structure for evolving healthcare needs
- Proper indexing for query performance
- Clear relationships between entities
- Built-in safety mechanisms for patient care
- Audit trail for compliance
- Scalability for future growth
