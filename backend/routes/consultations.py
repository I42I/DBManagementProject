from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("consultations", __name__)

def _iso_to_dt(s: str):
    try:
        s = s.replace("Z", "+00:00") if isinstance(s, str) and s.endswith("Z") else s
        dt = datetime.fromisoformat(s) if isinstance(s, str) else s
        if not isinstance(dt, datetime):
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def _validate(b):
    for f in ["patient_id", "doctor_id", "date_time"]:
        if f not in b:
            return f"{f} requis"
    if isinstance(b.get("date_time"), str) and not _iso_to_dt(b["date_time"]):
        return "date_time doit être au format ISO 8601"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db
    # cast ObjectId obligatoires
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    # existence basique
    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # facility_id requis par le schema → génère si absent
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        fid = ObjectId()

    # appointment_id optionnel + vérification d’existence si fourni
    ap_id = None
    if b.get("appointment_id"):
        try:
            ap_id = ObjectId(b["appointment_id"])
        except InvalidId:
            return {"error": "appointment_id doit être un ObjectId"}, 400
        if not db.appointments.find_one({"_id": ap_id}):
            return {"error": "appointment introuvable"}, 404

    # date/heure
    dt = _iso_to_dt(b["date_time"]) if isinstance(b.get("date_time"), str) else (
        b.get("date_time") or datetime.utcnow().replace(tzinfo=timezone.utc)
    )

    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": fid,
        "date_time": dt,
        "symptomes": b.get("symptomes"),
        "diagnostic": b.get("diagnostic"),
        "notes": b.get("notes"),
        "vital_signs": b.get("vital_signs"),
        "attachments": b.get("attachments"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }
    if ap_id:
        doc["appointment_id"] = ap_id

    try:
        ins = db.consultations.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return {"error": "validation_mongo", "details": details}, 400

    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id" in request.args:
            q["doctor_id"] = ObjectId(request.args["doctor_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    cur = current_app.db.consultations.find(q).sort("date_time", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.consultations.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

