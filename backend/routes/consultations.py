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
from datetime import datetime
from bson import ObjectId
from utils import strip_none, iso_to_dt, validate_objectid, check_exists

bp = Blueprint("consultations", __name__)


# -----------------------------------------------------------
# POST /api/consultations — créer une consultation
# -----------------------------------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    try:
        pid = validate_objectid(b.get("patient_id"), "patient_id")
        did = validate_objectid(b.get("doctor_id"), "doctor_id")
        dt = iso_to_dt(b.get("date_time"))
        if not dt:
            return {"error": "date_time requis et doit être au format ISO 8601"}, 400

        check_exists("patients", pid, "Patient")
        check_exists("doctors", did, "Médecin")

        fid = validate_objectid(b.get("facility_id")) if b.get("facility_id") else ObjectId()
        ap_id = validate_objectid(b.get("appointment_id")) if b.get("appointment_id") else None
        if ap_id:
            check_exists("appointments", ap_id, "Rendez-vous")

    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}, 400

    doc = strip_none({
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": fid,
        "appointment_id": ap_id,
        "date_time": dt,
        "symptomes": b.get("symptomes"),
        "diagnostic": b.get("diagnostic"),
        "notes": b.get("notes"),
        "vital_signs": b.get("vital_signs"),
        "attachments": b.get("attachments"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    ins = current_app.db.consultations.insert_one(doc)
    return {"_id": ins.inserted_id}, 201

# -----------------------------------------------------------
# GET /api/consultations — liste (filtres : patient/doctor/facility + période)
# -----------------------------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "patient_id" in request.args: q["patient_id"] = validate_objectid(request.args["patient_id"])
        if "doctor_id" in request.args: q["doctor_id"] = validate_objectid(request.args["doctor_id"])
        if "facility_id" in request.args: q["facility_id"] = validate_objectid(request.args["facility_id"])
    except ValueError as e:
        return {"error": str(e)}, 400

    date_from = iso_to_dt(request.args.get("date_from"))
    date_to = iso_to_dt(request.args.get("date_to"))
    if date_from or date_to:
        q["date_time"] = {}
        if date_from: q["date_time"]["$gte"] = date_from
        if date_to: q["date_time"]["$lte"] = date_to

    cur = current_app.db.consultations.find(q).sort("date_time", -1).limit(200)
    return list(cur)

# -----------------------------------------------------------
# GET /api/consultations/<id> — détail d'une consultation
# -----------------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = validate_objectid(id)
    except ValueError as e:
        return {"error": str(e)}, 400
    d = current_app.db.consultations.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)
