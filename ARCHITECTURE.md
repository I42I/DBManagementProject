# System Architecture Documentation

## Overview
This document provides detailed technical architecture for the Digitalization of Medical Services NoSQL project.

## Architecture Layers

### 1. Presentation Layer
The presentation layer handles all user interactions and provides different interfaces for various stakeholders.

#### Web Applications
- **Doctor Portal**: Desktop/tablet interface for consultations
- **Patient Portal**: Self-service appointment booking and record access
- **Pharmacy System**: Prescription verification and dispensing
- **Lab Portal**: Test result entry and management
- **Admin Dashboard**: System configuration and monitoring

#### Mobile Applications
- **Patient Mobile App**: iOS/Android native apps
- **Doctor Mobile App**: On-the-go access to patient records
- **Emergency Access App**: Quick access for ambulance/ER staff

#### Alternative Interfaces
- **SMS Interface**: Basic queries and reminders
- **USSD Interface**: Menu-driven access without internet
- **API Access**: Third-party integrations

### 2. API Gateway Layer
Centralized entry point for all client requests.

#### Responsibilities
- **Authentication**: JWT-based token validation
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: Prevent API abuse
- **Request Routing**: Direct requests to appropriate services
- **Load Balancing**: Distribute traffic across servers
- **API Versioning**: Support multiple API versions
- **Logging**: Request/response logging for auditing

#### Technologies
- **Gateway**: Kong / AWS API Gateway / Nginx
- **Load Balancer**: HAProxy / Nginx
- **Cache**: Redis for session management

### 3. Business Logic Layer
Core application services implementing healthcare workflows.

#### Microservices Architecture

##### Patient Service
- Patient registration and profile management
- Medical history tracking
- Allergy and chronic condition management
- Emergency contact information

##### Doctor Service
- Doctor profile and credentials
- Specialty and qualification management
- Schedule and availability
- Performance metrics

##### Consultation Service
- Consultation recording
- Diagnosis and treatment documentation
- Vital signs tracking
- Medical notes and observations

##### Prescription Service
- Digital prescription creation
- Safety checks (allergies, interactions, contraindications)
- Prescription tracking and refills
- Pharmacy integration

##### Appointment Service
- Appointment scheduling and booking
- Doctor availability checking
- Conflict resolution
- Reminder scheduling

##### Laboratory Service
- Test ordering workflow
- Result entry and verification
- Integration with lab equipment
- Result delivery to doctors

##### Notification Service
- SMS notification dispatch
- Email notifications
- Push notifications
- USSD menu generation
- Reminder scheduling

##### Payment Service
- Payment processing (Cash, Mobile Money)
- Invoice generation
- Payment history
- Receipt management
- Insurance claims (future)

##### Analytics Service
- Health statistics aggregation
- Anonymization of patient data
- Disease surveillance
- Reporting for health authorities

### 4. Data Layer
NoSQL database implementation for flexible and scalable data storage.

#### Database Choice: MongoDB

##### Advantages
- **Document Model**: Natural fit for medical records
- **Flexible Schema**: Easy to add new medical fields
- **Scalability**: Horizontal scaling with sharding
- **Replication**: High availability with replica sets
- **Aggregation**: Powerful analytics capabilities
- **Indexing**: Fast queries on patient records
- **Offline Sync**: MongoDB Realm for mobile apps

##### Collections Design
```
┌─────────────────────────────────────────────────────┐
│                MongoDB Database                     │
├─────────────────────────────────────────────────────┤
│  • patients        (Patient records)                │
│  • doctors         (Healthcare provider info)       │
│  • consultations   (Medical consultations)          │
│  • prescriptions   (Prescriptions)                  │
│  • appointments    (Scheduled appointments)         │
│  • laboratories    (Lab tests and results)          │
│  • notifications   (Alerts and reminders)           │
│  • payments        (Payment transactions)           │
│  • audit_logs      (System audit trail)             │
│  • health_stats    (Anonymized statistics)          │
└─────────────────────────────────────────────────────┘
```

##### Indexing Strategy
- Primary Index: `_id` (default)
- Patient Collection: `national_id`, `phone`, `name`
- Doctor Collection: `license_number`, `specialty`
- Consultation Collection: `patient_id`, `doctor_id`, `date`
- Prescription Collection: `patient_id`, `status`, `date_issued`
- Appointment Collection: `patient_id`, `doctor_id`, `scheduled_date`
- Compound Indexes: `{patient_id: 1, date: -1}` for recent history

##### Sharding Strategy
- Shard Key: `patient_id` for patient-centric queries
- Geographic sharding for multi-region deployment
- Range-based sharding for time-series data

### 5. Integration Layer
External service integrations and third-party APIs.

#### SMS Gateway Integration
- **Providers**: Twilio, AfricasTalking
- **Use Cases**: 
  - Appointment reminders
  - Medication reminders
  - Lab result notifications
  - Emergency alerts

#### USSD Integration
- **Menu Structure**:
  ```
  *123# - Main Menu
    1. Check Appointment
    2. Medication Reminder
    3. Lab Results
    4. Emergency Contact
  ```

#### Mobile Money Integration
- **Providers**: MTN Mobile Money, Orange Money, Airtel Money
- **Functions**:
  - Payment collection
  - Payment verification
  - Transaction status checking
  - Refunds processing

#### Health Authority Integration
- **Data Export**: Anonymized health statistics
- **Formats**: JSON, CSV, HL7 FHIR
- **Frequency**: Daily/Weekly/Monthly reports
- **Security**: Encrypted channels, API keys

### 6. Infrastructure Layer
Deployment and operational infrastructure.

#### Containerization
```yaml
# Docker Compose Structure
services:
  - api-gateway (Nginx)
  - patient-service
  - doctor-service
  - consultation-service
  - prescription-service
  - appointment-service
  - laboratory-service
  - notification-service
  - payment-service
  - analytics-service
  - mongodb-primary
  - mongodb-secondary-1
  - mongodb-secondary-2
  - redis-cache
  - rabbitmq
```

#### High Availability Setup
```
                    ┌──────────────┐
                    │ Load Balancer│
                    └───────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
    ┌───────┐          ┌───────┐          ┌───────┐
    │ API-1 │          │ API-2 │          │ API-3 │
    └───┬───┘          └───┬───┘          └───┬───┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                ┌─────────────────────┐
                │  MongoDB Replica    │
                │  Primary + 2 Secondary│
                └─────────────────────┘
```

#### Monitoring & Logging
- **Metrics**: Prometheus + Grafana
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Alerting**: PagerDuty / Opsgenie
- **Health Checks**: Regular endpoint monitoring
- **Performance**: Application Performance Monitoring (APM)

## Data Flow Examples

### Example 1: Patient Consultation Flow
```
1. Patient arrives → Check-in (Reception)
2. Doctor accesses patient record
   ├─ Query: db.patients.findOne({_id: "PAT-001"})
   └─ Returns: Medical history, allergies, chronic conditions
3. Doctor performs consultation
   └─ Records: Diagnosis, vital signs, notes
4. Doctor creates prescription
   ├─ Safety Check: Verify against allergies
   ├─ Safety Check: Check chronic conditions
   └─ Save: db.prescriptions.insertOne({...})
5. Prescription sent to pharmacy
   └─ Notification: SMS to patient
6. Payment processing
   └─ Mobile Money transaction
7. Update patient record
   └─ db.patients.updateOne({_id: "PAT-001"}, {$set: {...}})
```

### Example 2: Emergency Access Flow
```
1. Patient arrives unconscious
2. Scan patient ID card / national ID
3. Emergency lookup
   └─ Query: db.patients.findOne({national_id: "..."})
4. Display critical info immediately:
   ├─ ⚠️ ALLERGIES
   ├─ ⚠️ CHRONIC CONDITIONS (DIABETES)
   ├─ Blood Type
   └─ Emergency Contact
5. Doctor makes informed decision
6. Log emergency access
   └─ db.audit_logs.insertOne({...})
```

### Example 3: Offline Sync Flow
```
1. Mobile app works offline
   └─ Local SQLite/Realm database
2. User performs actions
   ├─ Create consultation
   └─ Stored locally with sync flag
3. Connection detected
4. Background sync starts
   └─ Send pending records to server
5. Server validates and stores
6. Acknowledgment sent to client
7. Local sync flags cleared
```

## Security Architecture

### Authentication Flow
```
1. User Login → API Gateway
2. Validate Credentials → User Service
3. Generate JWT Token (15 min expiry)
4. Refresh Token (7 days expiry)
5. Return tokens to client
6. Client includes JWT in headers
   Authorization: Bearer <token>
7. API Gateway validates token
8. Route to appropriate service
```

### Authorization Model
```
Roles:
├─ ADMIN
│  └─ Full system access
├─ DOCTOR
│  ├─ View patient records
│  ├─ Create consultations
│  ├─ Create prescriptions
│  └─ Order lab tests
├─ NURSE
│  ├─ View patient records
│  ├─ Record vital signs
│  └─ Schedule appointments
├─ PHARMACIST
│  ├─ View prescriptions
│  └─ Mark as dispensed
├─ LAB_TECH
│  ├─ View test orders
│  └─ Enter results
├─ PATIENT
│  ├─ View own records
│  └─ Book appointments
└─ RECEPTIONIST
   └─ Patient registration
```

### Data Encryption
- **At Rest**: AES-256 encryption for sensitive fields
- **In Transit**: TLS 1.3 for all communications
- **Database**: MongoDB encrypted storage engine
- **Backups**: Encrypted backup files
- **Logs**: Sensitive data masked in logs

### Audit Trail
Every data access and modification is logged:
```json
{
  "timestamp": "2024-03-20T14:30:00Z",
  "user_id": "DOC-001",
  "action": "VIEW_PATIENT",
  "resource_id": "PAT-001",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "SUCCESS"
}
```

## Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: All microservices are stateless
- **Load Balancing**: Round-robin across service instances
- **Database Sharding**: Partition data by patient_id
- **Caching**: Redis for frequently accessed data

### Performance Optimization
- **Database Indexing**: Optimize query performance
- **Caching Strategy**: Cache patient records (5 min TTL)
- **CDN**: Static assets served via CDN
- **Compression**: Gzip compression for API responses
- **Pagination**: Limit result sets to 50 records

### Capacity Planning
```
Expected Load (Year 1):
- Patients: 100,000
- Doctors: 500
- Daily Consultations: 2,000
- Daily Prescriptions: 1,800
- Database Size: ~50 GB
- API Requests: 100,000/day

Scaling Strategy:
- 3 API servers (2 active, 1 standby)
- 3-node MongoDB replica set
- Redis cluster (3 nodes)
- Auto-scaling based on CPU > 70%
```

## Disaster Recovery

### Backup Strategy
- **Full Backup**: Daily at 2 AM
- **Incremental Backup**: Every 6 hours
- **Retention**: 30 days
- **Location**: Off-site encrypted storage
- **Test Restore**: Monthly verification

### Failover Process
1. Primary database failure detected
2. Automatic promotion of secondary to primary
3. DNS updated to new primary
4. Monitor and alert operations team
5. Investigate and repair failed node
6. Restore replica set configuration

### Business Continuity
- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 15 minutes
- **Redundancy**: Multi-region deployment
- **Manual Override**: Paper-based emergency procedures

## Compliance & Standards

### Healthcare Standards
- **HL7 FHIR**: Fast Healthcare Interoperability Resources
- **ICD-10**: International Classification of Diseases
- **LOINC**: Logical Observation Identifiers Names and Codes
- **SNOMED CT**: Systematized Nomenclature of Medicine

### Data Protection
- **HIPAA**: Health Insurance Portability and Accountability Act
- **GDPR**: General Data Protection Regulation
- **Local Laws**: Comply with national healthcare regulations
- **Data Sovereignty**: Data stored within country boundaries

## Deployment Pipeline

### CI/CD Workflow
```
1. Developer commits code → GitHub
2. Automated tests run (Unit, Integration)
3. Code quality checks (ESLint, SonarQube)
4. Security scanning (Snyk, OWASP)
5. Build Docker images
6. Push to container registry
7. Deploy to staging environment
8. Automated smoke tests
9. Manual approval gate
10. Deploy to production
11. Post-deployment verification
```

### Environment Strategy
- **Development**: Local Docker Compose
- **Testing**: Automated test environment
- **Staging**: Production-like environment
- **Production**: High-availability cluster

## Conclusion
This architecture provides a robust, scalable, and secure foundation for the digitalization of medical services, with special consideration for low-connectivity environments and healthcare-specific requirements.
