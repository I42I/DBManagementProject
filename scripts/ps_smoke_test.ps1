<#  Smoke test end-to-end de toutes les routes  #>
param(
  [string]$Base = "http://localhost:5000",
  [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSCommandPath
Set-Location $root\..

$API = "$Base/api"
$results = @()
function Add-Res($name, $ok, $status, $detail) {
  $results += [pscustomobject]@{ Step=$name; OK=$ok; Status=$status; Detail=$detail }
  if ($Verbose) { Write-Host "[$name] OK=$ok Status=$status Detail=$detail" }
}

function Try-Req {
  param(
    [string]$Method, [string]$Url, $BodyObj = $null
  )
  try {
    if ($BodyObj -ne $null) {
      $json = $BodyObj | ConvertTo-Json -Depth 10
      $resp = Invoke-RestMethod -Uri $Url -Method $Method -Body $json -ContentType 'application/json'
    } else {
      $resp = Invoke-RestMethod -Uri $Url -Method $Method
    }
    return ,@($true, 200, $resp)
  } catch {
    # Essaye d'extraire le code
    $code = 0
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
      $code = [int]$_.Exception.Response.StatusCode
    }
    $body = $_.ErrorDetails.Message
    if (-not $body) { $body = $_.Exception.Message }
    return ,@($false, $code, $body)
  }
}

# 1) Health
for ($i=0; $i -lt 25; $i++) {
  $ok,$st,$r = Try-Req GET "$Base/health"
  if ($ok -and $r.status -eq "ok") { break }
  Start-Sleep -Milliseconds 300
}
Add-Res "health" $ok $st ($ok ? "up" : $r)

if (-not $ok) {
  $results | Format-Table
  exit 1
}

# Ids communs
$facility = "000000000000000000000001" # si tu veux forcer un ObjectId fixe
# 2) Patient
$body = @{
  facility_id = $facility
  identite = @{ prenom="Alice"; nom="Durand"; date_naissance="1990-01-01T00:00:00Z"; sexe="F" }
  contacts = @{ phone="0611223344"; email="alice@example.com" }
}
$ok,$st,$r = Try-Req POST "$API/patients" $body
Add-Res "patient:POST" $ok $st $r
if (-not $ok) { $results | Format-Table; exit 1 }
$PID = $r._id

# 3) Doctor
$body = @{
  facility_id = $facility
  identite = @{ prenom="Dr"; nom="House" }
  specialites = @("general")
}
$ok,$st,$r = Try-Req POST "$API/doctors" $body
Add-Res "doctor:POST" $ok $st $r
if (-not $ok) { $results | Format-Table; exit 1 }
$DID = $r._id

# 4) Appointment
$body = @{
  patient_id = $PID; doctor_id = $DID; facility_id=$facility
  date_time  = "2025-11-01T09:00:00Z"; status="scheduled"; reason="checkup"
}
$ok,$st,$r = Try-Req POST "$API/appointments" $body
Add-Res "appointments:POST" $ok $st $r
$APPT = if ($ok) { $r._id } else { $null }

# 5) Consultation
$body = @{
  patient_id=$PID; doctor_id=$DID; facility_id=$facility
  date_time="2025-11-01T09:30:00Z"; symptomes="fièvre"; diagnostic="infection virale"
  appointment_id=$APPT
}
$ok,$st,$r = Try-Req POST "$API/consultations" $body
Add-Res "consultations:POST" $ok $st $r
$CONS = if ($ok) { $r._id } else { $null }

# 6) Prescription
$body = @{
  patient_id=$PID; doctor_id=$DID; consultation_id=$CONS
  items = @(@{ dci="PARACETAMOL"; posologie="1g x3/j"; quantity=6 })
  notes = "boire de l'eau"
}
$ok,$st,$r = Try-Req POST "$API/prescriptions" $body
Add-Res "prescriptions:POST" $ok $st $r
$PRES = if ($ok) { $r._id } else { $null }

# 7) Laboratory
$body = @{
  patient_id=$PID; doctor_id=$DID; facility_id=$facility; status="ordered"
  tests = @(@{ code="CRP"; name="CRP"; status="ordered" })
}
$ok,$st,$r = Try-Req POST "$API/laboratories" $body
Add-Res "laboratories:POST" $ok $st $r
$LAB = if ($ok) { $r._id } else { $null }

# 8) Pharmacy
$body = @{
  patient_id=$PID; doctor_id=$DID; facility_id=$facility; status="requested"
  prescription_id=$PRES
  items=@(@{ dci="PARACETAMOL"; qty=6 })
}
$ok,$st,$r = Try-Req POST "$API/pharmacies" $body
Add-Res "pharmacies:POST" $ok $st $r
$PHAR = if ($ok) { $r._id } else { $null }

# 9) Payment
$body = @{
  patient_id=$PID; facility_id=$facility; amount=15000; currency="XAF"; status="pending"
  appointment_id=$APPT
}
$ok,$st,$r = Try-Req POST "$API/payments" $body
Add-Res "payments:POST" $ok $st $r
$PAY = if ($ok) { $r._id } else { $null }

# 10) Notification
$body = @{
  channel="sms"; status="queued"; to_patient_id=$PID; ref_type="appointment"; ref_id=$APPT
  payload=@{ msg="Rappel RDV 09:00" }; send_at="2025-10-31T18:00:00Z"
}
$ok,$st,$r = Try-Req POST "$API/notifications" $body
Add-Res "notifications:POST" $ok $st $r
$NOTI = if ($ok) { $r._id } else { $null }

# 11) Health authority report
$body = @{
  facility_id=$facility; report_type="case_summary"; status="draft"
  period_start="2025-10-01T00:00:00Z"; period_end="2025-10-31T23:59:59Z"
  payload=@{ cases=42; notes="octobre" }
}
$ok,$st,$r = Try-Req POST "$API/health_authorities" $body
Add-Res "health_authorities:POST" $ok $st $r
$HA = if ($ok) { $r._id } else { $null }

# --- Quelques GET / PATCH rapides ---
$null = Try-Req GET "$API/appointments?patient_id=$PID"
$null = Try-Req GET "$API/prescriptions?patient_id=$PID"
$ok,$st,$r = Try-Req PATCH "$API/pharmacies/$PHAR" @{ status="dispensed" }
Add-Res "pharmacies:PATCH->dispensed" $ok $st $r
$ok,$st,$r = Try-Req PATCH "$API/payments/$PAY" @{ status="paid" }
Add-Res "payments:PATCH->paid" $ok $st $r
$ok,$st,$r = Try-Req PATCH "$API/notifications/$NOTI" @{ status="sent" }
Add-Res "notifications:PATCH->sent" $ok $st $r

# Résumé & sortie
$results | Tee-Object -Variable table | Format-Table -AutoSize
$out = @{
  when = (Get-Date)
  base = $Base
  results = $results
  ids = @{ patient=$PID; doctor=$DID; appointment=$APPT; consultation=$CONS; prescription=$PRES; lab=$LAB; pharmacy=$PHAR; payment=$PAY; notification=$NOTI; health_report=$HA }
}
$out | ConvertTo-Json -Depth 10 | Out-File -FilePath "scripts\last_smoke_results.json" -Encoding utf8

$failed = $results | Where-Object { -not $_.OK }
if ($failed.Count -gt 0) { exit 2 } else { exit 0 }

