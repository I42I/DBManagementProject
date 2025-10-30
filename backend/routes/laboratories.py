from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime

bp = Blueprint("laboratories", __name__)

_ALLOWED_STATUS = {"ordered", "in_progress", "completed", "cancelled"}

def _strip_none(d: dict):
    """Supprime les None au 1er niveau (évite d’écrire null)."""
    return {k: v for k, v in d.items() if v is not None}

def _validate(b):
    for f in ("patient_id", "doctor_id", "status"):
        if f not in b:
            return f"{f} requis"
    if b["status"] not in _ALLOWED_STATUS:
        return "status invalide (ordered|in_progress|completed|cancelled)"
    # tests optionnels, mais si fournis : objets avec code/name/status
    if "tests" in b:
        if not isinstance(b["tests"], list):
            return "tests doit être un tableau"
        for t in b["tests"]:
            if not isinstance(t, dict):
                return "chaque test doit être un objet"
            for k in ("code", "name", "status"):
                if k not in t:
                    return f"tests[].{k} requis"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db
    # cast ids + existence
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # facility_id (généré si absent)
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        fid = ObjectId()

    # appointment_id optionnel
    ap_id = None
    if b.get("appointment_id"):
        try:
            ap_id = ObjectId(b["appointment_id"])
        except InvalidId:
            return {"error": "appointment_id doit être un ObjectId"}, 400

    # tests normalisés
    tests = []
    for t in b.get("tests", []):
        nt = {
            "code": t.get("code"),
            "name": t.get("name"),
            "status": t.get("status"),
        }
        for k in ("result", "unit", "ref_range", "abnormal"):
            if t.get(k) is not None:
                nt[k] = t[k]
        tests.append(_strip_none(nt))

    now = datetime.utcnow()
    date_reported = now if b.get("status") == "completed" else None

    doc = _strip_none({
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": fid,
        "appointment_id": ap_id,      # supprimé si None par _strip_none
        "status": b.get("status", "ordered"),
        "date_ordered": now,
        "date_reported": date_reported,
        "tests": tests if tests else None,
        "notes": b.get("notes"),
        "created_at": now,
        "updated_at": now,
        "deleted": False
    })

    try:
        ins = db.laboratories.insert_one(doc)
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
    if "status" in request.args:
        q["status"] = request.args["status"]

    cur = current_app.db.laboratories.find(q).sort("date_ordered", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.laboratories.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

