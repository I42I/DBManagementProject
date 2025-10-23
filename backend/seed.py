# seed.py — indices + import du seed_data.json en respectant tes validateurs
import os, json
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import ASCENDING

SEED_FILE = os.getenv("SEED_FILE", "seed_data.json")

# -----------------------------
# Helpers date / cast
# -----------------------------
def _to_dt(v):
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str):
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    return None

def get_or_create_facility_id(db, code_or_id):
    """
    facility_id doit être un ObjectId (validator).
    Si une string 24 hexa -> cast en ObjectId.
    Sinon on considère un 'code' (ex: 'HOSP-001') -> upsert dans db.facilities et on renvoie son _id.
    """
    if isinstance(code_or_id, ObjectId):
        return code_or_id
    if isinstance(code_or_id, str) and len(code_or_id) == 24:
        try:
            return ObjectId(code_or_id)
        except Exception:
            pass
    code = code_or_id or "HOSP-001"
    fac = db.facilities.find_one({"code": code}, {"_id": 1})
    if not fac:
        res = db.facilities.insert_one({"code": code, "name": f"Facility {code}"})
        return res.inserted_id
    return fac["_id"]

# -----------------------------
# Normalisations selon validateurs
# -----------------------------
def normalize_patient(d, db):
    """
    Patient requis par validator:
      - created_at : date BSON
      - facility_id : ObjectId (vers 'facilities')
      - identite : { prenom, nom, date_naissance (date BSON), sexe in [M,F,X] }
    Legacy: first_name/last_name/birth_date -> mappés vers identite.*
    """
    d = dict(d)

    # created_at
    d["created_at"] = _to_dt(d.get("created_at")) or datetime.now(timezone.utc)

    # facility_id -> ObjectId
    d["facility_id"] = get_or_create_facility_id(db, d.get("facility_id") or "HOSP-001")

    # identite (support legacy keys both at root and nested inside identite)
    ident = d.get("identite") or {}
    # map legacy names if present at root
    if not ident.get("prenom") and d.get("first_name"): ident["prenom"] = d["first_name"]
    if not ident.get("nom") and d.get("last_name"): ident["nom"] = d["last_name"]
    # map legacy names if present inside ident itself
    if not ident.get("prenom") and ident.get("first_name"): ident["prenom"] = ident.get("first_name")
    if not ident.get("nom") and ident.get("last_name"): ident["nom"] = ident.get("last_name")

    # date_naissance (OBLIGATOIRE, type date) — accept birth_date either at root or inside ident
    if "date_naissance" in ident:
        ident["date_naissance"] = _to_dt(ident["date_naissance"]) or ident["date_naissance"]
    elif "birth_date" in ident:
        ident["date_naissance"] = _to_dt(ident["birth_date"]) or ident["birth_date"]
    else:
        ident["date_naissance"] = _to_dt(d.get("birth_date")) or datetime(2000, 1, 1, tzinfo=timezone.utc)

    # sexe autorisé M/F/X (par défaut X)
    sex = ident.get("sexe")
    if sex not in ("M", "F", "X"):
        ident["sexe"] = "X"

    ident.setdefault("prenom", "N/A")
    ident.setdefault("nom", "N/A")
    # remove legacy keys inside ident
    for k in ("first_name", "last_name", "birth_date"):
        if k in ident: ident.pop(k, None)
    d["identite"] = ident

    # cleanup legacy
    for k in ("first_name", "last_name", "birth_date"):
        d.pop(k, None)

    return d

def normalize_doctor(d, db):
    """
    Doctor requis par validator:
      - created_at : date BSON
      - facility_id : ObjectId
      - identite : { prenom, nom [, sexe in M/F/X] }
      - specialites : liste[str] (sinon default ["General Medicine"])
    Legacy: first_name/last_name/speciality|specialty -> remontés.
    """
    d = dict(d)

    # created_at
    d["created_at"] = _to_dt(d.get("created_at")) or datetime.now(timezone.utc)

    # facility_id
    d["facility_id"] = get_or_create_facility_id(db, d.get("facility_id") or "HOSP-001")

    # identite
    ident = d.get("identite") or {}
    if not ident.get("prenom") and d.get("first_name"):
        ident["prenom"] = d["first_name"]
    if not ident.get("nom") and d.get("last_name"):
        ident["nom"] = d["last_name"]
    sex = ident.get("sexe") or d.get("gender")
    if sex:
        sex = str(sex).upper()[:1]
        if sex not in ("M", "F", "X"):
            sex = "X"
        ident["sexe"] = sex
    ident.setdefault("prenom", "N/A")
    ident.setdefault("nom", "N/A")
    d["identite"] = ident

    # specialites (liste requise)
    specs = d.get("specialites")
    if not specs:
        for k in ("speciality", "specialty", "specialité", "spécialité"):
            if d.get(k):
                specs = d[k]
                break
    if isinstance(specs, str):
        specs = [specs]
    if not isinstance(specs, list) or len(specs) == 0:
        specs = ["General Medicine"]
    d["specialites"] = specs

    # cleanup legacy
    for k in ("first_name", "last_name", "speciality", "specialty", "specialité", "spécialité", "gender"):
        d.pop(k, None)

    return d


def normalize_notification(d, db):
    """
    Aligne un doc 'notifications' sur le validator:
      - channel ∈ {"sms","email","push"}
      - status  ∈ {"queued","sent","failed","read"}
      - created_at : date BSON
      - expires_at : date BSON (optionnel)
    Coercit les anciennes valeurs: system->push, pending->queued.
    """
    d = dict(d)

    # dates
    d["created_at"] = _to_dt(d.get("created_at")) or datetime.now(timezone.utc)
    if "expires_at" in d and isinstance(d["expires_at"], str):
        d["expires_at"] = _to_dt(d["expires_at"]) or d["expires_at"]

    # channel mapping
    raw_channel = (d.get("channel") or "").lower()
    if raw_channel == "system":
        raw_channel = "push"
    if raw_channel not in ("sms", "email", "push"):
        raw_channel = "email"  # défaut valide
    d["channel"] = raw_channel

    # status mapping
    raw_status = (d.get("status") or "").lower()
    if raw_status == "pending":
        raw_status = "queued"
    if raw_status not in ("queued", "sent", "failed", "read"):
        raw_status = "queued"  # défaut valide
    d["status"] = raw_status

    return d



# -----------------------------
# Indexes (partiels sur uniques)
# -----------------------------
def ensure_indexes(db):
    db.patients.create_index(
        [("email", ASCENDING)],
        name="uniq_email_not_null",
        unique=True,
        partialFilterExpression={"email": {"$type": "string"}}
    )
    db.doctors.create_index(
        [("license_number", ASCENDING)],
        name="uniq_license_not_null",
        unique=True,
        partialFilterExpression={"license_number": {"$type": "string"}}
    )
    db.appointments.create_index(
        [("patient_id", ASCENDING), ("start_at", ASCENDING)],
        name="uniq_patient_start",
        unique=True
    )
    db.notifications.create_index(
        "expires_at",
        name="ttl_expires_at",
        expireAfterSeconds=0
    )

# -----------------------------
# Upsert générique + résolutions
# -----------------------------
def upsert_many(db, coll_name, docs, key, bypass_validation=False):
    if not docs:
        return
    coll = db[coll_name]
    for d in docs:
        d = dict(d)
        for k in ("start_at", "expires_at", "updated_at", "created_at"):
            if k in d and isinstance(d[k], str):
                d[k] = _to_dt(d[k]) or d[k]
        for k in ("patient_id", "doctor_id"):
            if k in d and isinstance(d[k], str) and len(d[k]) == 24:
                try:
                    d[k] = ObjectId(d[k])
                except Exception:
                    pass
        # coerce facility_id codes/strings into ObjectId using helper
        if "facility_id" in d:
            try:
                d["facility_id"] = get_or_create_facility_id(db, d["facility_id"])
            except Exception:
                # if coercion fails, leave as-is and let validation/reporting handle it
                pass
        coll.update_one(
            {key: d[key]},
            {"$set": d},
            upsert=True,
            bypass_document_validation=bypass_validation
        )

def resolve_ids_for_appointments(db, docs):
    if not docs:
        return []
    out = []
    for d in docs:
        d = dict(d)
        if "start_at" in d and isinstance(d["start_at"], str):
            d["start_at"] = _to_dt(d["start_at"]) or d["start_at"]
        if "patient_email" in d and "patient_id" not in d:
            p = db.patients.find_one({"email": d["patient_email"]}, {"_id": 1})
            if p:
                d["patient_id"] = p["_id"]
        if "doctor_license" in d and "doctor_id" not in d:
            doc = db.doctors.find_one({"license_number": d["doctor_license"]}, {"_id": 1})
            if doc:
                d["doctor_id"] = doc["_id"]
        out.append(d)
    return out

# -----------------------------
# Chargement du seed
# -----------------------------
def load_seed(db):
    if not os.path.exists(SEED_FILE):
        print(f"[seed] {SEED_FILE} not found. Skip.")
        return
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # patients -> normaliser selon validator
    patients_raw = data.get("patients", [])
    patients = [normalize_patient(x, db) for x in patients_raw]
    upsert_many(db, "patients", patients, "email")

    # doctors -> normaliser selon validator
    doctors_raw = data.get("doctors", [])
    doctors = [normalize_doctor(x, db) for x in doctors_raw]
    upsert_many(db, "doctors", doctors, "license_number")

    # annuaires
    upsert_many(db, "pharmacies", data.get("pharmacies", []), "name")
    upsert_many(db, "laboratories", data.get("laboratories", []), "name")
    upsert_many(db, "healthauthorities", data.get("healthauthorities", []), "name")

   # notifications
    notifications_raw = data.get("notifications", [])
    notifications = [normalize_notification(x, db) for x in notifications_raw]
    upsert_many(db, "notifications", notifications, "_seed_id")

    # appointments (résolution par email/licence)
    apps = resolve_ids_for_appointments(db, data.get("appointments", []))
    upsert_many(db, "appointments", apps, "_seed_id")

    # prescriptions / payments
    upsert_many(db, "prescriptions", data.get("prescriptions", []), "_seed_id")
    upsert_many(db, "payments", data.get("payments", []), "_seed_id")

    print("[seed] Done.")

# -----------------------------
# Main (optionnel en CLI)
# -----------------------------
def main(db=None):
    from pymongo import MongoClient
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME   = os.getenv("MONGO_DB", "hospital")
    if db is None:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
    ensure_indexes(db)
    if os.getenv("SEED_ON_START", "false").lower() in ("1","true","yes"):
        load_seed(db)
    print("[seed] Indexes OK. Conditional seed done.")

if __name__ == "__main__":
    main()

