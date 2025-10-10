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

## 📋 Database Description

This project uses a **NoSQL database** (MongoDB) to handle the flexible and scalable nature of medical data. The database is designed to accommodate various entities with dynamic schemas that can evolve over time.

### Database Schema

#### Collections

**patients**
```json
{
  "_id": "ObjectId",
  "firstName": "string",
  "lastName": "string",
  "dateOfBirth": "date",
  "gender": "string",
  "phone": "string",
  "email": "string",
  "address": {
    "street": "string",
    "city": "string",
    "country": "string"
  },
  "medicalHistory": {
    "allergies": ["string"],
    "chronicConditions": ["string"],
    "bloodType": "string"
  },
  "createdAt": "timestamp",
  "updatedAt": "timestamp"
}
```

**doctors**
```json
{
  "_id": "ObjectId",
  "firstName": "string",
  "lastName": "string",
  "specialty": "string",
  "licenseNumber": "string",
  "phone": "string",
  "email": "string",
  "availableHours": ["string"],
  "createdAt": "timestamp"
}
```

**appointments**
```json
{
  "_id": "ObjectId",
  "patientId": "ObjectId",
  "doctorId": "ObjectId",
  "dateTime": "timestamp",
  "status": "string", // "scheduled", "completed", "cancelled"
  "reason": "string",
  "createdAt": "timestamp"
}
```

**consultations**
```json
{
  "_id": "ObjectId",
  "appointmentId": "ObjectId",
  "patientId": "ObjectId",
  "doctorId": "ObjectId",
  "diagnosis": "string",
  "treatment": "string",
  "notes": "string",
  "vitalSigns": {
    "temperature": "number",
    "bloodPressure": "string",
    "pulse": "number"
  },
  "createdAt": "timestamp"
}
```

**prescriptions**
```json
{
  "_id": "ObjectId",
  "consultationId": "ObjectId",
  "patientId": "ObjectId",
  "doctorId": "ObjectId",
  "medications": [
    {
      "name": "string",
      "dosage": "string",
      "frequency": "string",
      "duration": "string",
      "contraindications": ["string"]
    }
  ],
  "alerts": ["string"],
  "status": "string", // "pending", "dispensed", "completed"
  "createdAt": "timestamp"
}
```

**pharmacies**
```json
{
  "_id": "ObjectId",
  "name": "string",
  "address": "string",
  "phone": "string",
  "license": "string",
  "inventory": [
    {
      "medicationName": "string",
      "quantity": "number",
      "expiryDate": "date"
    }
  ]
}
```

**laboratories**
```json
{
  "_id": "ObjectId",
  "patientId": "ObjectId",
  "testType": "string",
  "results": "string",
  "datePerformed": "timestamp",
  "performedBy": "string",
  "status": "string" // "pending", "completed"
}
```

**notifications**
```json
{
  "_id": "ObjectId",
  "recipientId": "ObjectId",
  "recipientType": "string", // "patient", "doctor"
  "type": "string", // "appointment", "medication", "test_result"
  "message": "string",
  "sentAt": "timestamp",
  "delivered": "boolean"
}
```

**payments**
```json
{
  "_id": "ObjectId",
  "patientId": "ObjectId",
  "consultationId": "ObjectId",
  "amount": "number",
  "currency": "string",
  "method": "string", // "cash", "mobile_money", "card"
  "status": "string", // "pending", "completed", "failed"
  "transactionId": "string",
  "createdAt": "timestamp"
}
```

### Data Relationships

The database uses **references** (ObjectIds) to link related documents across collections:
- Appointments reference both Patient and Doctor
- Consultations reference Appointments, Patients, and Doctors
- Prescriptions reference Consultations, Patients, and Doctors
- Laboratory tests reference Patients
- Notifications reference either Patients or Doctors
- Payments reference Patients and Consultations

### Indexing Strategy

Key indexes for performance optimization:
- `patients`: email (unique), phone
- `doctors`: email (unique), specialty
- `appointments`: patientId, doctorId, dateTime
- `consultations`: patientId, doctorId, appointmentId
- `prescriptions`: patientId, consultationId, status
- `notifications`: recipientId, type, sentAt

## 🚀 Deployment Instructions

### Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (if running locally without Docker)
- MongoDB 6.0+ (if running locally without Docker)

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_ORG/DBManagementProject.git
   cd DBManagementProject
   ```

2. **Build and start the containers**
   ```bash
   docker-compose up -d
   ```

3. **Verify the services are running**
   ```bash
   docker-compose ps
   ```

4. **Access the application**
   - API: http://localhost:3000
   - MongoDB: mongodb://localhost:27017

5. **View logs**
   ```bash
   docker-compose logs -f
   ```

6. **Stop the services**
   ```bash
   docker-compose down
   ```

### Option 2: Local Deployment

1. **Clone and install dependencies**
   ```bash
   git clone https://github.com/YOUR_ORG/DBManagementProject.git
   cd DBManagementProject
   npm install
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection string and other settings
   ```

3. **Start MongoDB**
   ```bash
   # On Linux/Mac
   mongod --dbpath /data/db
   
   # Or use a cloud MongoDB instance (MongoDB Atlas)
   ```

4. **Start the application**
   ```bash
   npm start
   ```

5. **Run in development mode**
   ```bash
   npm run dev
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/medical_services
MONGODB_DB_NAME=medical_services

# API Configuration
PORT=3000
NODE_ENV=production

# SMS/USSD Integration
SMS_API_KEY=your_sms_api_key
SMS_PROVIDER=africastalking  # Or use 'twilio' for alternative provider

# Security
JWT_SECRET=your_jwt_secret_key
JWT_EXPIRY=24h

# Offline Mode
ENABLE_OFFLINE_MODE=true
SYNC_INTERVAL=300000
```

### Production Deployment

For production deployment on cloud platforms:

**AWS/Azure/GCP:**
1. Set up a managed MongoDB instance (MongoDB Atlas, AWS DocumentDB)
2. Deploy the application using container services (ECS, AKS, GKE)
3. Configure load balancer and auto-scaling
4. Set up monitoring and alerting
5. Configure backup and disaster recovery

**Heroku:**
```bash
heroku create medical-services-app
heroku addons:create mongolab
git push heroku main
```

### Database Initialization

Initialize the database with sample data:

```bash
npm run seed
```

Or manually import data:

```bash
mongoimport --db medical_services --collection patients --file seeds/patients.json
mongoimport --db medical_services --collection doctors --file seeds/doctors.json
```

## 📡 API Query Examples

The API follows RESTful principles and returns JSON responses.

### Base URL
```
http://localhost:3000/api/v1
```

### Authentication

All API requests require authentication using JWT tokens:

```bash
# Login to get token
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "doctor@example.com", "password": "password123"}'

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123",
    "email": "doctor@example.com",
    "role": "doctor"
  }
}
```

Use the token in subsequent requests:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/v1/patients
```

### Patient Endpoints

**Create a new patient**
```bash
# Note: Phone numbers use +237 (Cameroon) as an example - adapt to your region
curl -X POST http://localhost:3000/api/v1/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1980-05-15",
    "gender": "male",
    "phone": "+237699123456",
    "email": "john.doe@example.com",
    "address": {
      "street": "123 Main St",
      "city": "Douala",
      "country": "Cameroon"
    },
    "medicalHistory": {
      "allergies": ["penicillin", "aspirin"],
      "chronicConditions": ["diabetes", "hypertension"],
      "bloodType": "A+"
    }
  }'
```

**Get patient by ID**
```bash
curl -X GET http://localhost:3000/api/v1/patients/64a1b2c3d4e5f6789abcdef0 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update patient information**
```bash
curl -X PUT http://localhost:3000/api/v1/patients/64a1b2c3d4e5f6789abcdef0 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "phone": "+237699999999",
    "medicalHistory": {
      "allergies": ["penicillin", "aspirin"],
      "chronicConditions": ["diabetes", "hypertension"],
      "bloodType": "A+"
    }
  }'
```

**Search patients**
```bash
# Search by name
curl -X GET "http://localhost:3000/api/v1/patients?search=John" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by chronic condition
curl -X GET "http://localhost:3000/api/v1/patients?chronicCondition=diabetes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Doctor Endpoints

**Get all doctors**
```bash
curl -X GET http://localhost:3000/api/v1/doctors \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get doctors by specialty**
```bash
curl -X GET "http://localhost:3000/api/v1/doctors?specialty=cardiology" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Appointment Endpoints

**Create an appointment**
```bash
curl -X POST http://localhost:3000/api/v1/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patientId": "64a1b2c3d4e5f6789abcdef0",
    "doctorId": "64a1b2c3d4e5f6789abcdef1",
    "dateTime": "2024-12-15T10:00:00Z",
    "reason": "Regular checkup"
  }'
```

**Get patient appointments**
```bash
curl -X GET "http://localhost:3000/api/v1/appointments?patientId=64a1b2c3d4e5f6789abcdef0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update appointment status**
```bash
curl -X PATCH http://localhost:3000/api/v1/appointments/64a1b2c3d4e5f6789abcdef2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "status": "completed"
  }'
```

### Consultation Endpoints

**Create a consultation**
```bash
curl -X POST http://localhost:3000/api/v1/consultations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "appointmentId": "64a1b2c3d4e5f6789abcdef2",
    "patientId": "64a1b2c3d4e5f6789abcdef0",
    "doctorId": "64a1b2c3d4e5f6789abcdef1",
    "diagnosis": "Type 2 Diabetes - well controlled",
    "treatment": "Continue metformin, increase exercise",
    "vitalSigns": {
      "temperature": 36.8,
      "bloodPressure": "120/80",
      "pulse": 72
    },
    "notes": "Patient is compliant with medication"
  }'
```

**Get patient's consultation history**
```bash
curl -X GET "http://localhost:3000/api/v1/consultations?patientId=64a1b2c3d4e5f6789abcdef0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Prescription Endpoints

**Create a prescription with safety checks**
```bash
curl -X POST http://localhost:3000/api/v1/prescriptions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "consultationId": "64a1b2c3d4e5f6789abcdef3",
    "patientId": "64a1b2c3d4e5f6789abcdef0",
    "doctorId": "64a1b2c3d4e5f6789abcdef1",
    "medications": [
      {
        "name": "Metformin",
        "dosage": "500mg",
        "frequency": "twice daily",
        "duration": "30 days",
        "contraindications": []
      },
      {
        "name": "Aspirin",
        "dosage": "81mg",
        "frequency": "once daily",
        "duration": "30 days",
        "contraindications": ["bleeding disorders"]
      }
    ]
  }'

# Response includes alerts if patient has contraindications
{
  "_id": "64a1b2c3d4e5f6789abcdef4",
  "alerts": [
    "⚠️ Patient is allergic to aspirin - CONTRAINDICATED"
  ],
  "medications": [...],
  "status": "pending"
}
```

**Get prescription with safety verification**
```bash
curl -X GET http://localhost:3000/api/v1/prescriptions/64a1b2c3d4e5f6789abcdef4/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Laboratory Endpoints

**Order laboratory test**
```bash
curl -X POST http://localhost:3000/api/v1/laboratories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patientId": "64a1b2c3d4e5f6789abcdef0",
    "testType": "HbA1c",
    "performedBy": "Lab Technician 1",
    "status": "pending"
  }'
```

**Submit test results**
```bash
curl -X PATCH http://localhost:3000/api/v1/laboratories/64a1b2c3d4e5f6789abcdef5 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "results": "HbA1c: 6.5% (controlled)",
    "status": "completed"
  }'
```

### Notification Endpoints

**Send appointment reminder**
```bash
curl -X POST http://localhost:3000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "recipientId": "64a1b2c3d4e5f6789abcdef0",
    "recipientType": "patient",
    "type": "appointment",
    "message": "Reminder: You have an appointment tomorrow at 10:00 AM with Dr. Smith"
  }'
```

**Send medication reminder via SMS**
```bash
curl -X POST http://localhost:3000/api/v1/notifications/sms \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "phone": "+237699123456",
    "message": "Time to take your Metformin medication (500mg)"
  }'
```

### Payment Endpoints

**Process payment**
```bash
curl -X POST http://localhost:3000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patientId": "64a1b2c3d4e5f6789abcdef0",
    "consultationId": "64a1b2c3d4e5f6789abcdef3",
    "amount": 5000,
    "currency": "XAF",
    "method": "mobile_money"
  }'
```

**Get payment history**
```bash
curl -X GET "http://localhost:3000/api/v1/payments?patientId=64a1b2c3d4e5f6789abcdef0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Health Authority Endpoints (Anonymized Statistics)

**Get aggregated health statistics**
```bash
curl -X GET http://localhost:3000/api/v1/health-authority/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response
{
  "totalPatients": 1250,
  "chronicConditionsDistribution": {
    "diabetes": 320,
    "hypertension": 450,
    "asthma": 180
  },
  "consultationsPerMonth": 2400,
  "commonDiagnoses": [
    {"diagnosis": "Malaria", "count": 580},
    {"diagnosis": "Diabetes", "count": 320},
    {"diagnosis": "Hypertension", "count": 450}
  ],
  "prescriptionAlerts": 45
}
```

### Error Handling

All API endpoints return standard HTTP status codes and error messages:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid patient data",
    "details": [
      "dateOfBirth is required",
      "email must be valid"
    ]
  }
}
```

Common status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## 🤖 AI Usage

This section documents the use of AI tools in the development process, including prompts and corrections made.

### AI Tools Used

- **GitHub Copilot**: Code completion and generation
- **ChatGPT/GPT-4**: Architecture design, problem-solving, and documentation
- **AI-Assisted Code Review**: Code quality and security analysis

### Key Prompts and Use Cases

#### 1. Database Schema Design

**Prompt:**
```
Design a NoSQL database schema for a medical services platform that needs to:
- Store patient information including medical history, allergies, and chronic conditions
- Track appointments between patients and doctors
- Record consultations with diagnoses and treatments
- Manage prescriptions with safety alerts for contraindications
- Support offline mode and eventual consistency
- Work in low-connectivity environments (Africa context)

The schema should be optimized for MongoDB and include appropriate indexes.
```

**AI Response:** Generated the collections structure with proper relationships using ObjectId references and suggested indexing strategy.

**Corrections Made:**
- Added `bloodType` field to patient medical history (not suggested by AI initially)
- Modified `medications` array structure in prescriptions to include `contraindications` field
- Added `alerts` array at prescription level for runtime safety checks

#### 2. API Safety Mechanisms

**Prompt:**
```
How can I implement a safety mechanism to prevent prescribing contraindicated medications to patients with specific conditions like diabetes? For example, preventing glucose injection to diabetic patients.
```

**AI Response:** Suggested implementing middleware that checks patient medical history against medication contraindications before saving prescriptions.

**Implementation:**
```javascript
// Middleware to check contraindications
async function checkMedicationSafety(req, res, next) {
  const patient = await Patient.findById(req.body.patientId);
  const alerts = [];
  
  req.body.medications.forEach(med => {
    // Check against patient allergies
    if (patient.medicalHistory.allergies.includes(med.name.toLowerCase())) {
      alerts.push(`⚠️ Patient is allergic to ${med.name} - CONTRAINDICATED`);
    }
    
    // Check chronic condition contraindications
    patient.medicalHistory.chronicConditions.forEach(condition => {
      if (med.contraindications.includes(condition)) {
        alerts.push(`⚠️ ${med.name} is contraindicated for ${condition}`);
      }
    });
  });
  
  req.body.alerts = alerts;
  next();
}
```

**Corrections Made:**
- Added case-insensitive comparison for allergy checking
- Included both allergies and chronic condition contraindications
- Changed from blocking the request to adding warnings (to allow doctor override in emergencies)

#### 3. Offline Mode Implementation

**Prompt:**
```
Design an offline-first architecture for a medical app that works in areas with poor internet connectivity. The app should sync data when connectivity is available.
```

**AI Response:** Suggested using service workers, IndexedDB for local storage, and a sync queue mechanism.

**Corrections Made:**
- Changed from service workers to a simpler approach using local MongoDB replica for initial version
- Added conflict resolution strategy for when same patient data is modified offline by multiple users
- Implemented timestamp-based "last write wins" strategy with audit logs

#### 4. SMS/USSD Integration

**Prompt:**
```
How can I integrate SMS notifications for appointment reminders and medication alerts in a Node.js application for users in Africa?
```

**AI Response:** Recommended using Twilio or Africa's Talk API for SMS, with USSD for feature phones.

**Implementation Decision:**
- Chose Africa's Talk for better coverage in Africa
- Added fallback to basic SMS if USSD unavailable
- Implemented rate limiting to control costs

**Corrections Made:**
- AI suggested sending all notifications immediately, changed to batch processing every 5 minutes
- Added character limit handling for SMS (160 characters)
- Implemented retry mechanism with exponential backoff

#### 5. Data Privacy and HIPAA Compliance

**Prompt:**
```
What security measures should I implement for a medical database containing patient health information?
```

**AI Response:** Provided list including encryption at rest, encryption in transit, access controls, audit logs, and data anonymization for statistics.

**Corrections Made:**
- AI didn't mention field-level encryption for sensitive data; added encryption for medical history fields
- Added automatic data anonymization when accessed by health authority endpoints
- Implemented stricter role-based access control (RBAC) than AI suggested

#### 6. Error Handling and Validation

**Prompt:**
```
Create comprehensive input validation for patient registration API endpoint including email, phone number (Cameroon format), and date of birth validation.
```

**AI Response:** Generated validation schemas using Joi.

**Corrections Made:**
```javascript
// AI suggested generic email validation
email: Joi.string().email()

// Corrected to handle local email formats
email: Joi.string().email().optional() // Made optional for low-literacy users

// AI suggested US phone format
phone: Joi.string().pattern(/^\+1[0-9]{10}$/)

// Corrected to Cameroon format
phone: Joi.string().pattern(/^\+237[0-9]{9}$/).required()
```

#### 7. MongoDB Aggregation for Statistics

**Prompt:**
```
Write MongoDB aggregation pipeline to generate anonymized statistics for health authority including chronic condition distribution and common diagnoses.
```

**AI Response:** Provided basic aggregation pipeline.

**Corrections Made:**
- AI used `$group` without `$project` to remove patient identifiers; added proper anonymization stage
- Added date filtering to get statistics for specific time periods
- Optimized pipeline by adding `$match` stage early to reduce processed documents

### Lessons Learned

#### What AI Did Well:
- Generated boilerplate code quickly
- Provided good starting point for database schema
- Suggested appropriate libraries and frameworks
- Helped with documentation structure

#### What Needed Human Correction:
- **Context-specific requirements**: AI didn't fully understand African context (phone formats, connectivity issues, local payment methods)
- **Security considerations**: Required more robust security measures than AI suggested
- **Edge cases**: Many edge cases not covered in initial AI-generated code
- **Business logic**: AI couldn't determine correct behavior for medical safety checks without explicit guidance
- **Performance optimization**: AI generated working but not optimized code

#### Best Practices for Using AI:
1. **Use AI for scaffolding**, not final implementation
2. **Always review and test** AI-generated code thoroughly
3. **Provide detailed context** in prompts (e.g., "in African context with poor connectivity")
4. **Iterate on prompts** when first response isn't adequate
5. **Combine AI suggestions** with domain expertise and security best practices
6. **Document all changes** made to AI-generated code
7. **Never blindly trust** AI for security-critical or medical-critical code

### AI-Assisted Debugging Examples

#### Bug 1: Race Condition in Appointment Booking

**Issue:** Multiple users could book the same appointment slot.

**AI Debugging Prompt:**
```
I have a race condition where two patients can book the same doctor appointment slot at the same time. Here's my current code: [code snippet]
```

**AI Solution:** Suggested using MongoDB transactions with optimistic locking.

**Final Implementation:** Used pessimistic locking with a distributed lock (Redis) as transactions alone weren't sufficient in high-concurrency scenarios.

#### Bug 2: Prescription Validation Not Working

**Issue:** Contraindication checks weren't triggering for medications with different name formats.

**AI Debugging Prompt:**
```
My medication contraindication check isn't working when medication names have different cases or spacing. How can I normalize medication names for comparison?
```

**AI Solution:** Suggested normalization function to lowercase and trim.

**Correction:** Extended to handle common variations (e.g., "aspirin" vs "acetylsalicylic acid") using a medication mapping table.

### Conclusion

AI tools significantly accelerated development but required careful human oversight, especially for:
- Medical safety features
- Security implementation
- Context-specific requirements
- Edge case handling
- Performance optimization

The key to effective AI usage is treating it as a powerful assistant, not a replacement for human expertise and judgment.
