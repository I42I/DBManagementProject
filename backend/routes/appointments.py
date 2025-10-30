from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("appointments", __name__)

_ALLOWED_STATUS = {"scheduled", "checked_in", "cancelled", "no_show", "completed"}

def _iso_to_dt(s: str):
    try:
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def _validate(b):
    for f in ["patient_id", "doctor_id", "date_time"]:
        if f not in b:
            return f"{f} requis"
    if not _iso_to_dt(b["date_time"]):
        return "date_time doit être au format ISO 8601"
    if "status" in b and b["status"] not in _ALLOWED_STATUS:
        return "status invalide (scheduled|checked_in|cancelled|no_show|completed)"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # facility_id requis par le schéma → générer si absent
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        fid = ObjectId()

    doc = {
        "patient_id": pid,
        "doctor_id":  did,
        "facility_id": fid,
        "date_time": _iso_to_dt(b["date_time"]),
        "status": b.get("status", "scheduled"),
        "reason": b.get("reason"),
        "notes": b.get("notes"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }

    try:
        ins = db.appointments.insert_one(doc)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "doctor_id" in request.args:
            q["doctor_id"] = ObjectId(request.args["doctor_id"])
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    if "status" in request.args:
        st = request.args["status"]
        if st not in _ALLOWED_STATUS:
            return {"error": "status invalide (scheduled|checked_in|cancelled|no_show|completed)"}, 400
        q["status"] = st

    # filtres de période (optionnels)
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
            if not df: return {"error": "date_from doit être ISO 8601"}, 400
            rng["$gte"] = df
        if date_to:
            dt_ = _to_dt(date_to)
            if not dt_: return {"error": "date_to doit être ISO 8601"}, 400
            rng["$lte"] = dt_
        q["date_time"] = rng

    cur = current_app.db.appointments.find(q).sort("date_time", 1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.appointments.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

