// Sample Data
const patients = [
    {
        id: 1,
        name: "Jean Dupont",
        age: 45,
        gender: "M",
        allergies: "Pénicilline",
        conditions: "Diabète type 2",
        phone: "+243 812 345 678"
    },
    {
        id: 2,
        name: "Marie Martin",
        age: 32,
        gender: "F",
        allergies: "Aucune",
        conditions: "Hypertension",
        phone: "+243 823 456 789"
    },
    {
        id: 3,
        name: "Pierre Bernard",
        age: 58,
        gender: "M",
        allergies: "Aspirine",
        conditions: "Diabète type 2, Hypertension",
        phone: "+243 834 567 890"
    },
    {
        id: 4,
        name: "Sophie Laurent",
        age: 28,
        gender: "F",
        allergies: "Aucune",
        conditions: "Aucune",
        phone: "+243 845 678 901"
    },
    {
        id: 5,
        name: "Ahmed Hassan",
        age: 67,
        gender: "M",
        allergies: "Iode",
        conditions: "Diabète type 2, Insuffisance rénale",
        phone: "+243 856 789 012"
    }
];

const doctors = [
    { id: 1, name: "Dr. Kamau", specialty: "Cardiologie" },
    { id: 2, name: "Dr. Okonkwo", specialty: "Médecine générale" },
    { id: 3, name: "Dr. Diallo", specialty: "Endocrinologie" },
    { id: 4, name: "Dr. Mensah", specialty: "Pédiatrie" }
];

const consultations = [
    {
        id: 1,
        doctorId: 1,
        doctorName: "Dr. Kamau",
        patientId: 2,
        patientName: "Marie Martin",
        date: "2025-10-08",
        diagnosis: "Hypertension contrôlée",
        treatment: "Continuer le traitement actuel"
    },
    {
        id: 2,
        doctorId: 2,
        doctorName: "Dr. Okonkwo",
        patientId: 1,
        patientName: "Jean Dupont",
        date: "2025-10-07",
        diagnosis: "Contrôle diabète",
        treatment: "Ajustement insuline"
    },
    {
        id: 3,
        doctorId: 3,
        doctorName: "Dr. Diallo",
        patientId: 3,
        patientName: "Pierre Bernard",
        date: "2025-10-06",
        diagnosis: "Diabète mal contrôlé",
        treatment: "Modification traitement"
    },
    {
        id: 4,
        doctorId: 2,
        doctorName: "Dr. Okonkwo",
        patientId: 4,
        patientName: "Sophie Laurent",
        date: "2025-10-05",
        diagnosis: "Consultation de routine",
        treatment: "Aucun traitement nécessaire"
    },
    {
        id: 5,
        doctorId: 1,
        doctorName: "Dr. Kamau",
        patientId: 5,
        patientName: "Ahmed Hassan",
        date: "2025-10-04",
        diagnosis: "Insuffisance cardiaque",
        treatment: "Hospitalisation recommandée"
    }
];

const patientHistory = {
    1: [
        {
            date: "2025-10-07",
            type: "Consultation",
            doctor: "Dr. Okonkwo",
            diagnosis: "Contrôle diabète",
            treatment: "Ajustement insuline",
            notes: "Patient répond bien au traitement"
        },
        {
            date: "2025-09-15",
            type: "Analyse laboratoire",
            doctor: "Dr. Diallo",
            diagnosis: "Glycémie élevée",
            treatment: "HbA1c: 8.2%",
            notes: "Nécessite surveillance accrue"
        },
        {
            date: "2025-08-20",
            type: "Consultation",
            doctor: "Dr. Okonkwo",
            diagnosis: "Diabète type 2",
            treatment: "Metformine 500mg 2x/jour",
            notes: "Première consultation pour diabète"
        }
    ],
    2: [
        {
            date: "2025-10-08",
            type: "Consultation",
            doctor: "Dr. Kamau",
            diagnosis: "Hypertension contrôlée",
            treatment: "Continuer le traitement actuel",
            notes: "Tension: 130/85 mmHg"
        },
        {
            date: "2025-09-10",
            type: "Consultation",
            doctor: "Dr. Kamau",
            diagnosis: "Hypertension",
            treatment: "Amlodipine 5mg/jour",
            notes: "Tension initiale: 150/95 mmHg"
        }
    ],
    3: [
        {
            date: "2025-10-06",
            type: "Consultation",
            doctor: "Dr. Diallo",
            diagnosis: "Diabète mal contrôlé",
            treatment: "Modification traitement",
            notes: "HbA1c: 9.5% - Risque cardiovasculaire élevé"
        },
        {
            date: "2025-09-20",
            type: "Analyse laboratoire",
            doctor: "Dr. Diallo",
            diagnosis: "Hypertension non contrôlée",
            treatment: "Créatinine élevée: 150 μmol/L",
            notes: "Début d'insuffisance rénale"
        }
    ]
};

// Utility Functions
function highlightNavigation() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage || (currentPage === '' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
}

// Patient List Functions
function renderPatients(patientsToRender = patients) {
    const tbody = document.getElementById('patients-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    
    patientsToRender.forEach(patient => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${patient.id}</td>
            <td>${patient.name}</td>
            <td>${patient.age}</td>
            <td>${patient.gender}</td>
            <td>${patient.allergies}</td>
            <td>${patient.conditions}</td>
            <td>
                <a href="patient-history.html?id=${patient.id}" class="btn btn-small">Historique</a>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function searchPatients(searchTerm) {
    const filtered = patients.filter(patient => 
        patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.conditions.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.allergies.toLowerCase().includes(searchTerm.toLowerCase())
    );
    renderPatients(filtered);
}

// Consultation Functions
function renderConsultations(consultationsToRender = consultations) {
    const tbody = document.getElementById('consultations-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    
    consultationsToRender.forEach(consultation => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${consultation.date}</td>
            <td>${consultation.doctorName}</td>
            <td>${consultation.patientName}</td>
            <td>${consultation.diagnosis}</td>
            <td>${consultation.treatment}</td>
        `;
        tbody.appendChild(row);
    });
}

function filterConsultations(doctorId) {
    if (doctorId === '') {
        renderConsultations(consultations);
    } else {
        const filtered = consultations.filter(c => c.doctorId === parseInt(doctorId));
        renderConsultations(filtered);
    }
}

function populateDoctorFilter() {
    const select = document.getElementById('doctor-filter');
    if (!select) return;

    doctors.forEach(doctor => {
        const option = document.createElement('option');
        option.value = doctor.id;
        option.textContent = `${doctor.name} - ${doctor.specialty}`;
        select.appendChild(option);
    });
}

// Patient History Functions
function renderPatientHistory() {
    const params = new URLSearchParams(window.location.search);
    const patientId = parseInt(params.get('id')) || 1;
    
    const patient = patients.find(p => p.id === patientId);
    const history = patientHistory[patientId] || [];

    // Render patient info
    const patientInfoDiv = document.getElementById('patient-info');
    if (patientInfoDiv && patient) {
        patientInfoDiv.innerHTML = `
            <h2>Informations du Patient</h2>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Nom</span>
                    <span class="info-value">${patient.name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Âge</span>
                    <span class="info-value">${patient.age} ans</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Sexe</span>
                    <span class="info-value">${patient.gender}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Téléphone</span>
                    <span class="info-value">${patient.phone}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Allergies</span>
                    <span class="info-value ${patient.allergies !== 'Aucune' ? 'badge badge-warning' : ''}">${patient.allergies}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Conditions médicales</span>
                    <span class="info-value ${patient.conditions !== 'Aucune' ? 'badge badge-info' : ''}">${patient.conditions}</span>
                </div>
            </div>
        `;
    }

    // Render history timeline
    const timelineDiv = document.getElementById('history-timeline');
    if (timelineDiv) {
        timelineDiv.innerHTML = '<h2>Historique Médical</h2>';
        
        if (history.length === 0) {
            timelineDiv.innerHTML += '<p>Aucun historique disponible pour ce patient.</p>';
        } else {
            history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <h3>${item.type}</h3>
                    <div class="date">${item.date} - ${item.doctor}</div>
                    <div class="details">
                        <p><strong>Diagnostic:</strong> ${item.diagnosis}</p>
                        <p><strong>Traitement:</strong> ${item.treatment}</p>
                        <p><strong>Notes:</strong> ${item.notes}</p>
                    </div>
                `;
                timelineDiv.appendChild(historyItem);
            });
        }
    }

    // Update patient selector
    const patientSelect = document.getElementById('patient-select');
    if (patientSelect) {
        patients.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = p.name;
            if (p.id === patientId) {
                option.selected = true;
            }
            patientSelect.appendChild(option);
        });
    }
}

function changePatient(patientId) {
    window.location.href = `patient-history.html?id=${patientId}`;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    highlightNavigation();

    // Initialize based on current page
    if (document.getElementById('patients-tbody')) {
        renderPatients();
        
        const searchInput = document.getElementById('patient-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchPatients(e.target.value);
            });
        }
    }

    if (document.getElementById('consultations-tbody')) {
        populateDoctorFilter();
        renderConsultations();
        
        const doctorFilter = document.getElementById('doctor-filter');
        if (doctorFilter) {
            doctorFilter.addEventListener('change', (e) => {
                filterConsultations(e.target.value);
            });
        }
    }

    if (document.getElementById('patient-info')) {
        renderPatientHistory();
        
        const patientSelect = document.getElementById('patient-select');
        if (patientSelect) {
            patientSelect.addEventListener('change', (e) => {
                changePatient(e.target.value);
            });
        }
    }
});
