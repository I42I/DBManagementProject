param([string]$Base="http://127.0.0.1:5000")

# --------------------------------------------------------------------------
# Helpers (avec -ErrorAction Stop pour fail-fast)
# --------------------------------------------------------------------------
# --- Helpers robustes ---
function Ok($cond, $msg) {
  if (-not $cond) { Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }
  else { Write-Host "✅ $msg" -ForegroundColor Green }
}

function Show-HttpError($label, $err) {
  Write-Host "❌ $label" -ForegroundColor Red
  Write-Error $err.Exception.Message
  if ($err.Exception.Response) {
    try {
      $r = New-Object IO.StreamReader ($err.Exception.Response.GetResponseStream())
      Write-Error ("Response body: " + $r.ReadToEnd())
    } catch {}
  }
  exit 1
}

function IRMGET($url) {
  try   { Invoke-RestMethod -Uri $url -Method GET -ErrorAction Stop }
  catch { Show-HttpError "GET $url" $_ }
}

function IRMPOST($url, $body) {
  try {
    $json = $body | ConvertTo-Json -Depth 8
    Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json" -Body $json -ErrorAction Stop
  } catch { Show-HttpError "POST $url" $_ }
}

function IRMPATCH($url, $body) {
  try {
    $json = $body | ConvertTo-Json -Depth 8
    Invoke-RestMethod -Uri $url -Method PATCH -ContentType "application/json" -Body $json -ErrorAction Stop
  } catch { Show-HttpError "PATCH $url" $_ }
}

function IRMDELETE($url) {
  try   { Invoke-RestMethod -Uri $url -Method DELETE -ErrorAction Stop }
  catch { Show-HttpError "DELETE $url" $_ }
}

# Utilitaire pour “faire une étape” avec message OK automatique
function Step($label, [scriptblock]$action) {
  $global:LASTRESULT = & $action
  Write-Host "✅ $label" -ForegroundColor Green
}

Write-Host "=== CRUD full smoke on $Base ===" -f Cyan

# (Option) corriger les caractères d'affichage dans la console
try { chcp 65001 | Out-Null } catch {}

# --------------------------------------------------------------------------
# HEALTH
# --------------------------------------------------------------------------
$r = IRMGET "$Base/api/health"
Ok ($r.status -eq "ok") "Health OK"

# --------------------------------------------------------------------------
# PATIENTS (P1 à garder, P2 à supprimer)
# --------------------------------------------------------------------------
$P1 = IRMPOST "$Base/api/patients" @{
  identite = @{ prenom="Amina"; nom="Saleh"; date_naissance="1998-09-09T00:00:00Z"; sexe="F" }
  contacts = @{ phone = "+235 66 00 00 00" }
}
Ok ($P1._id) "Patient created"
$P1_id = $P1._id

$P1_full = IRMGET "$Base/api/patients/$P1_id"
Ok ($P1_full._id -eq $P1_id) "Patient get by id OK"
$facility_id = $P1_full.facility_id

$plist = IRMGET "$Base/api/patients"
Ok ($plist.Count -ge 1) "Patients list OK"

$upd = IRMPATCH "$Base/api/patients/$P1_id" @{ contacts = @{ phone = "+235 66 11 22 33" } }
Ok ($upd.matched -eq 1) "Patient patch OK"

$P2 = IRMPOST "$Base/api/patients" @{
  identite = @{ prenom="Issa"; nom="Yaya"; date_naissance="2001-05-10T00:00:00Z"; sexe="M" }
  contacts = @{ phone = "+32 470 00 00 00" }
}
$P2_id = $P2._id
$del = IRMDELETE "$Base/api/patients/$P2_id"
Ok ($del.deleted -eq $true) "Patient soft delete OK"

# --------------------------------------------------------------------------
# DOCTORS (D1 à garder)
# --------------------------------------------------------------------------
$D1 = IRMPOST "$Base/api/doctors" @{
  identite = @{ prenom="Ali"; nom="Karim" }
  specialites = @("cardiologie","medecine-generale")
}
Ok ($D1._id) "Doctor created"
$D1_id = $D1._id

$D1_full = IRMGET "$Base/api/doctors/$D1_id"
Ok ($D1_full._id -eq $D1_id) "Doctor get by id OK"

$dl = IRMGET "$Base/api/doctors"
Ok ($dl.Count -ge 1) "Doctors list OK"

$dup = IRMPATCH "$Base/api/doctors/$D1_id" @{ specialites = @("cardiologie","urgentiste") }
Ok ($dup.matched -eq 1) "Doctor patch OK"

# --------------------------------------------------------------------------
# APPOINTMENTS
# --------------------------------------------------------------------------
$Ap1 = IRMPOST "$Base/api/appointments" @{
  patient_id = $P1_id
  doctor_id  = $D1_id
  date_time  = (Get-Date).AddHours(2).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  status     = "scheduled"
  reason     = "Contrôle annuel"
}
Ok ($Ap1._id) "Appointment created"
$Ap1_id = $Ap1._id

$Ap1_get = IRMGET "$Base/api/appointments/$Ap1_id"
Ok ($Ap1_get._id -eq $Ap1_id) "Appointment get by id OK"

$apl = IRMGET "$Base/api/appointments"
Ok ($apl.Count -ge 1) "Appointments list OK"

$app_up = IRMPATCH "$Base/api/appointments/$Ap1_id" @{ status="completed" }
Ok ($app_up.matched -eq 1) "Appointment patch OK"

# --------------------------------------------------------------------------
# CONSULTATIONS
# --------------------------------------------------------------------------
$Cons1 = IRMPOST "$Base/api/consultations" @{
  patient_id = $P1_id
  doctor_id  = $D1_id
  appointment_id = $Ap1_id
  date_time  = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  symptomes  = "Fatigue légère"
  diagnostic = "RAS"
  notes      = "Hydratation + sommeil"
}
Ok ($Cons1._id) "Consultation created"
$Cons1_id = $Cons1._id

$c1 = IRMGET "$Base/api/consultations/$Cons1_id"
Ok ($c1._id -eq $Cons1_id) "Consultation get by id OK"

$cl = IRMGET "$Base/api/consultations"
Ok ($cl.Count -ge 1) "Consultations list OK"

$cup = IRMPATCH "$Base/api/consultations/$Cons1_id" @{ notes="Ajouter analyse sanguine" }
Ok ($cup.matched -eq 1) "Consultation patch OK"

# --------------------------------------------------------------------------
# PRESCRIPTIONS
# --------------------------------------------------------------------------
$Pres1 = IRMPOST "$Base/api/prescriptions" @{
  patient_id = $P1_id
  doctor_id  = $D1_id
  consultation_id = $Cons1_id
  items = @(@{ dci="Paracetamol"; posologie="500mg x3/j"; quantity=6 })
  notes = "3 jours"
}
Ok ($Pres1._id) "Prescription created"
$Pres1_id = $Pres1._id

$pr1 = IRMGET "$Base/api/prescriptions/$Pres1_id"
Ok ($pr1._id -eq $Pres1_id) "Prescription get by id OK"

$prl = IRMGET "$Base/api/prescriptions"
Ok ($prl.Count -ge 1) "Prescriptions list OK"

$prup = IRMPATCH "$Base/api/prescriptions/$Pres1_id" @{ notes="5 jours si douleur persiste" }
Ok ($prup.matched -eq 1) "Prescription patch OK"

# --------------------------------------------------------------------------
# PHARMACIES
# --------------------------------------------------------------------------
# après avoir obtenu $pId (patient) et $dId (doctor)
# --- CREATE ---
$ph = @{
  patient_id = $P1_id        # <--- bon ID patient
  doctor_id  = $D1_id        # <--- bon ID docteur
  status     = "requested"
  items      = @(@{ dci = "paracetamol"; qty = 1 })
}
$Ph1 = IRMPOST "$Base/api/pharmacies" $ph
Ok ($Ph1._id) "Pharmacy created"
$Ph1_id = $Ph1._id

# --- GET BY ID ---
$ph1 = IRMGET "$Base/api/pharmacies/$Ph1_id"
Ok ($ph1._id -eq $Ph1_id) "Pharmacy get by id OK"

# --- LIST ---
$phl = IRMGET "$Base/api/pharmacies"
Ok ($phl.Count -ge 1) "Pharmacies list OK"

# --- PATCH (dispense) ---
# (ton backend mettra dispensed_at automatiquement si absent — c’est ok)
$phup = IRMPATCH "$Base/api/pharmacies/$Ph1_id" @{ status = "dispensed" }
Ok ($phup.matched -eq 1) "Pharmacy patch OK"

# --------------------------------------------------------------------------
# LABORATORIES
# --------------------------------------------------------------------------
$Lab1 = IRMPOST "$Base/api/laboratories" @{
  # `name` is required by the collection validator; include it to avoid WriteError 121
  name = "Lab order for $P1_id"
  patient_id = $P1_id
  doctor_id  = $D1_id
  status = "ordered"
  tests = @(
    @{ code="CBC"; name="NFS"; status="ordered" },
    @{ code="GLU"; name="Glycémie"; status="ordered" }
  )
  notes = "A jeun"
}
Ok ($Lab1._id) "Laboratory created"
$Lab1_id = $Lab1._id

$lb1 = IRMGET "$Base/api/laboratories/$Lab1_id"
Ok ($lb1._id -eq $Lab1_id) "Laboratory get by id OK"

$lbl = IRMGET "$Base/api/laboratories"
Ok ($lbl.Count -ge 1) "Laboratories list OK"

$lup = IRMPATCH "$Base/api/laboratories/$Lab1_id" @{ status="completed"; notes="RAS" }
Ok ($lup.matched -eq 1) "Laboratory patch OK"

# --------------------------------------------------------------------------
# PAYMENTS
# --------------------------------------------------------------------------
$Pay1 = IRMPOST "$Base/api/payments" @{
  patient_id = $P1_id
  facility_id = $facility_id
  amount = 45.50
  currency = "EUR"
  status = "pending"
  method = "cash"
  items = @(
    @{ label="Consultation"; amount=30.00 },
    @{ label="Analyses NFS"; amount=15.50 }
  )
}
Ok ($Pay1._id) "Payment created"
$Pay1_id = $Pay1._id

$py1 = IRMGET "$Base/api/payments/$Pay1_id"
Ok ($py1._id -eq $Pay1_id) "Payment get by id OK"

$pyl = IRMGET "$Base/api/payments"
Ok ($pyl.Count -ge 1) "Payments list OK"

$pyup = IRMPATCH "$Base/api/payments/$Pay1_id" @{ status="paid" }
Ok ($pyup.matched -eq 1) "Payment patch OK"

# --------------------------------------------------------------------------
# NOTIFICATIONS  (ajout de template string pour respecter le schema)
# --------------------------------------------------------------------------
$N1 = IRMPOST "$Base/api/notifications" @{
  channel  = "email"
  status   = "queued"
  ref_type = "payment"
  ref_id   = $Pay1_id
  template = "payment_receipt"   # <= IMPORTANT pour éviter template=null
  payload  = @{}
}
Ok ($N1._id) "Notification created"
$N1_id = $N1._id

$n1 = IRMGET "$Base/api/notifications/$N1_id"
Ok ($n1._id -eq $N1_id) "Notification get by id OK"

$nl = IRMGET "$Base/api/notifications"
Ok ($nl.Count -ge 1) "Notifications list OK"

$nup = IRMPATCH "$Base/api/notifications/$N1_id" @{ status="sent" }
Ok ($nup.matched -eq 1) "Notification patch OK"

# --------------------------------------------------------------------------
# HEALTH AUTHORITIES
# --------------------------------------------------------------------------
$start = (Get-Date).AddDays(-7).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$end   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$HA1 = IRMPOST "$Base/api/health_authorities" @{
  # use an allowed report_type that matches the collection $jsonSchema
  report_type  = "case_summary"
  period_start = $start
  period_end   = $end
  status       = "draft"
  facility_id  = $facility_id
  payload      = @{ patients=1; consultations=1; labs=1; payments=1 }
}
Ok ($HA1._id) "HealthAuthorities created"
$HA1_id = $HA1._id

$ha1 = IRMGET "$Base/api/health_authorities/$HA1_id"
Ok ($ha1._id -eq $HA1_id) "HealthAuthorities get by id OK"

$hal = IRMGET "$Base/api/health_authorities"
Ok ($hal.Count -ge 1) "HealthAuthorities list OK"

$haup = IRMPATCH "$Base/api/health_authorities/$HA1_id" @{ status="submitted" }
Ok ($haup.matched -eq 1) "HealthAuthorities patch OK"

# --------------------------------------------------------------------------
# CLEANUP (optionnel)
# --------------------------------------------------------------------------
$ldel  = IRMDELETE "$Base/api/laboratories/$Lab1_id";       Ok ($ldel.deleted -eq $true) "Laboratory delete OK"
$phdel = IRMDELETE "$Base/api/pharmacies/$Ph1_id";          Ok ($phdel.deleted -eq $true) "Pharmacy delete OK"
$pyDel = IRMDELETE "$Base/api/payments/$Pay1_id";           Ok ($pyDel.deleted -eq $true) "Payment delete OK"
$nDel  = IRMDELETE "$Base/api/notifications/$N1_id";        Ok ($nDel.deleted -eq $true) "Notification delete OK"
$haDel = IRMDELETE "$Base/api/health_authorities/$HA1_id";  Ok ($haDel.deleted -eq $true) "HealthAuthorities delete OK"

Write-Host "🎉 ALL CRUD TESTS PASSED" -f Green
