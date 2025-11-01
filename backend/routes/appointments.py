# ===========================================================
#  appointments.py — Gestion des rendez-vous médicaux
#  Auteur : Yaya Issakha (ECAM - projet NoSQL)
#  Description :
#    Ce module gère les opérations CRUD principales liées
#    aux rendez-vous (appointments) entre patients et médecins.
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

# Création du blueprint Flask
bp = Blueprint("appointments", __name__)

# Liste des statuts autorisés pour un rendez-vous
_ALLOWED_STATUS = {"scheduled", "checked_in", "cancelled", "no_show", "completed"}


# -----------------------------------------------------------
# Fonction utilitaire : conversion d'une chaîne ISO8601 → datetime
# -----------------------------------------------------------
def _iso_to_dt(s: str):
    """Convertit une date ISO8601 (avec ou sans 'Z') vers un objet datetime UTC."""
    try:
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


# -----------------------------------------------------------
# Fonction utilitaire : suppression des clés dont la valeur est None
# (pour éviter les erreurs de validation MongoDB)
# -----------------------------------------------------------
def _strip_none(d: dict) -> dict:
    """Supprime toutes les clés dont la valeur est None (None → clé absente)."""
    return {k: v for k, v in d.items() if v is not None}


# -----------------------------------------------------------
# Validation du corps JSON reçu lors d’une création
# -----------------------------------------------------------
def _validate(b):
    """Vérifie que les champs obligatoires sont présents et valides."""
    for f in ["patient_id", "doctor_id", "date_time"]:
        if f not in b:
            return f"{f} requis"
    if not _iso_to_dt(b["date_time"]):
        return "date_time doit être au format ISO 8601"
    if "status" in b and b["status"] not in _ALLOWED_STATUS:
        return "status invalide (scheduled|checked_in|cancelled|no_show|completed)"
    return None


# -----------------------------------------------------------
# Route POST /api/appointments — création d’un rendez-vous
# -----------------------------------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # Étape 1 : validation des champs de base
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # Étape 2 : conversion des identifiants en ObjectId
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    # Étape 3 : vérification que le patient et le médecin existent bien
    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # Étape 4 : facility_id obligatoire selon ton schéma → générer si absent
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        fid = ObjectId()  # généré automatiquement si non fourni

    # Étape 5 : constitution du document Mongo
    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": fid,
        "date_time": _iso_to_dt(b["date_time"]),
        "status": b.get("status", "scheduled"),
        "reason": b.get("reason"),
        "notes": b.get("notes"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }

    # ⚠️ Étape 6 : suppression des champs None (clé supprimée au lieu de valeur null)
    print("[APPT DOC BEFORE STRIP]", doc)
    doc = _strip_none(doc)

    # Étape 7 : insertion en base
    try:
        print("[APPT DOC AFTER  STRIP]", doc)
        ins = db.appointments.insert_one(doc)
    except WriteError as we:
        # Si le validator Mongo rejette le document, on renvoie l’erreur complète
        return {
            "error": "validation_mongo",
            "details": getattr(we, "details", {}) or {}
        }, 400

    # Étape 8 : réponse OK
    return {"_id": str(ins.inserted_id)}, 201


# -----------------------------------------------------------
# Route GET /api/appointments — liste filtrable des rendez-vous
# -----------------------------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres possibles dans l’URL (ex: ?patient_id=...&doctor_id=...)
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

    # Filtres de date optionnels (date_from, date_to)
    def _to_dt(s):
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
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

    # Pipeline d’agrégation pour enrichir avec les infos du patient
    pipeline = [
        {"$match": q},
        {"$sort": {"date_time": 1}},
        {"$limit": 200},
        {"$lookup": {
            "from": "patients",
            "localField": "patient_id",
            "foreignField": "_id",
            "as": "p"
        }},
        {"$addFields": {
            "patient_name": {
                "$trim": {
                    "input": {
                        "$concat": [
                            {"$ifNull": [{"$arrayElemAt": ["$p.identite.prenom", 0]}, ""]},
                            " ",
                            {"$ifNull": [{"$arrayElemAt": ["$p.identite.nom", 0]}, ""]}
                        ]
                    }
                }
            },
            "patient_identifier": {"$ifNull": [{"$arrayElemAt": ["$p.identifiant", 0]}, ""]}
        }},
        {"$project": {"p": 0}}
    ]

    cur = current_app.db.appointments.aggregate(pipeline)
    return [d for d in cur], 200


# -----------------------------------------------------------
# Route GET /api/appointments/<id> — détail d’un rendez-vous
# -----------------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400

    d = current_app.db.appointments.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)
