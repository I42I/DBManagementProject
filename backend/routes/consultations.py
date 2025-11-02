# ===========================================================
#  consultations.py — Gestion des consultations médicales
#  
#  Rôle :
#    - Créer une consultation (patient ↔ médecin, notes, symptômes…)
#    - Lister les consultations (avec filtres)
#    - Récupérer le détail d'une consultation
#  Points clés :
#    - Conversion ISO8601 → datetime (UTC)
#    - Validation de types pour les champs optionnels
#    - Suppression des clés à None pour satisfaire le validator Mongo
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("consultations", __name__)

# -----------------------------------------------------------
# Utils : conversion ISO8601 → datetime(UTC)
# -----------------------------------------------------------
def _iso_to_dt(s: str):
    """Convertit une chaîne ISO8601 (avec/sans 'Z') en datetime UTC."""
    try:
        s = s.replace("Z", "+00:00") if isinstance(s, str) and s.endswith("Z") else s
        dt = datetime.fromisoformat(s) if isinstance(s, str) else s
        if not isinstance(dt, datetime):
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

# -----------------------------------------------------------
# Utils : supprimer les clés None (évite d'écrire `null`)
# -----------------------------------------------------------
def _strip_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}

# -----------------------------------------------------------
# Validation "champs obligatoires" + format date
# -----------------------------------------------------------
def _validate(b):
    for f in ["patient_id", "doctor_id", "date_time"]:
        if f not in b:
            return f"{f} requis"
    if isinstance(b.get("date_time"), str) and not _iso_to_dt(b["date_time"]):
        return "date_time doit être au format ISO 8601"
    return None

# -----------------------------------------------------------
# POST /api/consultations — créer une consultation
# -----------------------------------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # Validation minimale (présence + date ISO)
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # Cast ObjectId obligatoires
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    # existence patient/médecin
    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # facility_id (requis par ton schéma) → générer si absent
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        fid = ObjectId()

    #  appointment_id optionnel (et vérification d’existence si fourni)
    ap_id = None
    if b.get("appointment_id"):
        try:
            ap_id = ObjectId(b["appointment_id"])
        except InvalidId:
            return {"error": "appointment_id doit être un ObjectId"}, 400
        if not db.appointments.find_one({"_id": ap_id}):
            return {"error": "appointment introuvable"}, 404

    # Date/heure de la consultation (UTC)
    dt = _iso_to_dt(b["date_time"]) if isinstance(b.get("date_time"), str) else (
        b.get("date_time") or datetime.utcnow().replace(tzinfo=timezone.utc)
    )

    # Validation "douce" des champs optionnels selon notre validator
    #   - symptomes / diagnostic / notes : string si présent
    #   - vital_signs : object/dict si présent
    #   - attachments : array/list si présent
    symptomes  = b.get("symptomes")
    diagnostic = b.get("diagnostic")
    notes      = b.get("notes")
    vital      = b.get("vital_signs")
    attach     = b.get("attachments")

    if symptomes is not None and not isinstance(symptomes, str):
        return {"error": "symptomes doit être une chaîne si présent"}, 400
    if diagnostic is not None and not isinstance(diagnostic, str):
        return {"error": "diagnostic doit être une chaîne si présent"}, 400
    if notes is not None and not isinstance(notes, str):
        return {"error": "notes doit être une chaîne si présent"}, 400
    if vital is not None and not isinstance(vital, dict):
        return {"error": "vital_signs doit être un objet si présent"}, 400
    if attach is not None and not isinstance(attach, list):
        return {"error": "attachments doit être un tableau si présent"}, 400

    # Constitution du document Mongo
    doc = {
        "patient_id":  pid,
        "doctor_id":   did,
        "facility_id": fid,
        "date_time":   dt,
        "symptomes":   symptomes,
        "diagnostic":  diagnostic,
        "notes":       notes,
        "vital_signs": vital,
        "attachments": attach,
        "created_at":  datetime.utcnow(),
        "updated_at":  datetime.utcnow(),
        "deleted":     False,
    }
    if ap_id:
        doc["appointment_id"] = ap_id

    # Retirer tous les None (évite `null` → validator KO)
    doc = _strip_none(doc)

    # Insertion
    try:
        ins = db.consultations.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return {"error": "validation_mongo", "details": details}, 400

    return {"_id": str(ins.inserted_id)}, 201

# -----------------------------------------------------------
# GET /api/consultations — liste (filtres : patient/doctor/facility + période)
# -----------------------------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres par identifiants
    try:
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id" in request.args:
            q["doctor_id"] = ObjectId(request.args["doctor_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    # Filtres de période (date_from, date_to) — optionnels
    def _to_dt(s):
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")
    if date_from or date_to:
        rng = {}
        if date_from:
            df = _to_dt(date_from)
            if not df:
                return {"error": "date_from doit être ISO 8601"}, 400
            rng["$gte"] = df
        if date_to:
            dt_ = _to_dt(date_to)
            if not dt_:
                return {"error": "date_to doit être ISO 8601"}, 400
            rng["$lte"] = dt_
        q["date_time"] = rng

    cur = current_app.db.consultations.find(q).sort("date_time", -1).limit(200)
    return [d for d in cur], 200

# -----------------------------------------------------------
# GET /api/consultations/<id> — détail d'une consultation
# -----------------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.consultations.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)
