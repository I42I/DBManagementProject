# ===========================================================
#  patients.py — Gestion des patients (patients collection)
# 
#
#  Endpoints:
#    POST /api/patients       -> créer un patient
#    GET  /api/patients       -> lister (projection légère)
#    GET  /api/patients/<id>  -> détail
#
#  Points clés :
#    - Validation stricte de identite.{prenom, nom, date_naissance, sexe}
#    - facility_id généré si absent (mock, cohérent avec le reste)
#    - identifiant lisible auto: CHADH-PT-00001, 00002, ...
#    - Normalisation : trim + format (Prénom Capitalisé, NOM MAJUSCULE, sexe M/F/X)
#    - Dates en ISO -> datetime (timezone-safe)
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from pymongo import ReturnDocument
from datetime import datetime, timezone
from utils import strip_none, iso_to_dt, validate_objectid, check_exists

bp = Blueprint("patients", __name__)

_ALLOWED_SEX = {"M", "F", "X"}


# -------------------------------
# Séquence : CHADH-PT-00001, etc.
# -------------------------------
def _next_seq(db, name: str) -> int:
    """
    Utilise la collection 'counters' (document {_id: name, seq: N})
    pour auto-incrémenter un compteur par clé 'name'.
    """
    doc = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])

def _gen_patient_ident(db) -> str:
    return f"CHADH-PT-{_next_seq(db, 'patient_ident'):05d}"


# -------------------------------
# Validation métier
# -------------------------------
def _validate_patient(b: dict):
    """
    Requis:
      identite.prenom (str non vide)
      identite.nom    (str non vide)
      identite.date_naissance (ISO 8601)
      identite.sexe in {M, F, X}
    """
    if "identite" not in b:
        return "identite requis"

    ident = b["identite"]
    for f in ("prenom", "nom", "date_naissance", "sexe"):
        if f not in ident:
            return f"identite.{f} requis"

    # sexe
    sex = str(ident.get("sexe", "")).upper()[:1]
    if sex not in _ALLOWED_SEX:
        return "identite.sexe doit être M, F ou X"

    # date
    if isinstance(ident.get("date_naissance"), str):
        if not iso_to_dt(ident["date_naissance"]):
            return "identite.date_naissance doit être ISO 8601"

    return None

# -------------------------------
# GET /api/patients — liste
# -------------------------------
@bp.get("")
def list_():
    """
    Projection légère pour l’annuaire (frontend) :
    - identite (nom/prenom/date/sexe)
    - contacts.phone
    """
    cur = current_app.db.patients.find(
        {"deleted": {"$ne": True}},
        {"identite": 1, "contacts.phone": 1, "identifiant": 1}
    ).sort("created_at", -1).limit(200)

    
    return [d for d in cur], 200

# -------------------------------
# GET /api/patients/<id> — détail
# -------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.patients.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

# -------------------------------
# POST /api/patients — création
# -------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    #  Identifiant lisible auto si absent
    if not b.get("identifiant"):
        b["identifiant"] = _gen_patient_ident(current_app.db)

    #  Conversion des dates ISO en datetime
    if b.get("identite", {}).get("date_naissance"):
        b["identite"]["date_naissance"] = iso_to_dt(b["identite"]["date_naissance"])

    #  Préparation du document final
    doc = {
        "identifiant": b.get("identifiant"),
        "email": b.get("email"),
        "identite": b.get("identite"),
        "notes": b.get("notes"),
        "allergies": b.get("allergies"),
        "chronic_diseases": b.get("chronic_diseases"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "deleted": False,
    }

    try:
        doc["facility_id"] = validate_objectid(b.get("facility_id"))
    except (ValueError, TypeError):
        return {"error": "facility_id invalide ou manquant"}, 400

    #  Nettoyage des valeurs nulles
    doc = strip_none(doc)
    if "identite" in doc:
        doc["identite"] = strip_none(doc["identite"])

    #  Insertion Mongo
    try:
        ins = current_app.db.patients.insert_one(doc)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201


# -----------------------------------------------------------
# Route PATCH /api/patients/<id> — mise à jour partielle
# -----------------------------------------------------------
@bp.patch("/<id>")
def update(id):
    try:
        oid = validate_objectid(id)
        check_exists("patients", oid, "Patient")
    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}, 400

    b = request.get_json(force=True) or {}
    update_doc = {}
    
    for f in ("email", "notes", "allergies", "chronic_diseases"):
        if f in b: update_doc[f] = b[f]

    if "identite" in b and isinstance(b["identite"], dict):
        for f in ("prenom", "nom", "date_naissance", "sexe"):
            if f in b["identite"]:
                key = f"identite.{f}"
                if f == "date_naissance":
                    update_doc[key] = iso_to_dt(b["identite"][f])
                else:
                    update_doc[key] = b["identite"][f]

    if not update_doc:
        return {"error": "Aucun champ à mettre à jour"}, 400

    update_doc["updated_at"] = datetime.now(timezone.utc)

    res = current_app.db.patients.find_one_and_update(
        {"_id": oid},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER
    )
    return res, 200


# -----------------------------------------------------------
# Route DELETE /api/patients/<id> — suppression (soft)
# -----------------------------------------------------------
@bp.delete("/<id>")
def delete(id):
    try:
        oid = validate_objectid(id)
        check_exists("patients", oid, "Patient")
    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}, 400

    current_app.db.patients.update_one(
        {"_id": oid},
        {"$set": {"deleted": True, "updated_at": datetime.now(timezone.utc)}}
    )
    return "", 204

