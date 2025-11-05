# ===========================================================
#  appointments.py — Gestion des rendez-vous médicaux
#  
#  Description :
#    Ce module gère les opérations CRUD principales liées
#    aux rendez-vous (appointments) entre patients et médecins.
# ===========================================================

from flask import Blueprint, request, current_app
from datetime import datetime
from bson import ObjectId
from utils import strip_none, iso_to_dt, validate_objectid, check_exists

bp = Blueprint("appointments", __name__)
_ALLOWED_STATUS = {"scheduled", "checked_in", "cancelled", "no_show", "completed"}


# -----------------------------------------------------------
# Route POST /api/appointments — création d’un rendez-vous
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
        status = b.get("status", "scheduled")
        if status not in _ALLOWED_STATUS:
            return {"error": f"status invalide"}, 400

    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}, 400

    doc = strip_none({
        "patient_id": pid, "doctor_id": did, "facility_id": fid,
        "date_time": dt, "status": status,
        "reason": b.get("reason"), "notes": b.get("notes"),
        "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
    })

    ins = current_app.db.appointments.insert_one(doc)
    return {"_id": ins.inserted_id}, 201


# -----------------------------------------------------------
# Route GET /api/appointments — liste filtrable des rendez-vous
# -----------------------------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "doctor_id" in request.args: q["doctor_id"] = validate_objectid(request.args["doctor_id"])
        if "patient_id" in request.args: q["patient_id"] = validate_objectid(request.args["patient_id"])
        if "status" in request.args: q["status"] = request.args["status"]
        
        date_from = iso_to_dt(request.args.get("date_from"))
        date_to = iso_to_dt(request.args.get("date_to"))
        if date_from or date_to:
            q["date_time"] = {}
            if date_from: q["date_time"]["$gte"] = date_from
            if date_to: q["date_time"]["$lte"] = date_to
    except ValueError as e:
        return {"error": str(e)}, 400

    pipeline = [
        {"$match": q},
        {"$sort": {"date_time": 1}},
        {"$limit": 200},
        {"$lookup": {"from": "patients", "localField": "patient_id", "foreignField": "_id", "as": "p"}},
        {"$addFields": {
            "patient_name": {"$concat": [{"$arrayElemAt": ["$p.identite.prenom", 0]}, " ", {"$arrayElemAt": ["$p.identite.nom", 0]}]},
            "patient_identifier": {"$ifNull": [{"$arrayElemAt": ["$p.identifiant", 0]}, ""]}
        }},
        {"$project": {"p": 0}}
    ]
    cur = current_app.db.appointments.aggregate(pipeline)
    return list(cur), 200


# -----------------------------------------------------------
# Route GET /api/appointments/<id> — détail d’un rendez-vous
# -----------------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = validate_objectid(id)
    except ValueError as e:
        return {"error": str(e)}, 400
    doc = current_app.db.appointments.find_one({"_id": oid})
    return (doc, 200) if doc else ({"error": "introuvable"}, 404)
