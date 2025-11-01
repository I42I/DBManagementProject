# ===========================================================
#  patients.py — Gestion des patients (patients collection)
#  Auteur : Yaya Issakha — ECAM (Projet NoSQL)
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

bp = Blueprint("patients", __name__)

_ALLOWED_SEX = {"M", "F", "X"}

# -------------------------------
# Helpers génériques
# -------------------------------
def _strip_none(d: dict):
    """Supprime les paires clé=None (propre avant insertion Mongo)."""
    return {k: v for k, v in d.items() if v is not None}

def _iso_to_dt(s: str):
    """Parse une date ISO 8601 en datetime *timezone-aware* (UTC)."""
    try:
        s = s.replace("Z", "+00:00") if isinstance(s, str) and s.endswith("Z") else s
        dt = datetime.fromisoformat(s) if isinstance(s, str) else s
        if not isinstance(dt, datetime):
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

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
    n = _next_seq(db, "patient_ident")
    return f"CHADH-PT-{n:05d}"

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
        if not _iso_to_dt(ident["date_naissance"]):
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

    # NOTE : On renvoie tel quel comme dans tes autres routes.
    # Si tu veux JSON-safe partout, on pourra uniformiser avec jsonify + cast.
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

    # 1) Validation fonctionnelle
    err = _validate_patient(b)
    if err:
        return {"error": err}, 400

    # 2) facility_id requis par le $jsonSchema → cast ou génération mock
    if b.get("facility_id"):
        try:
            b["facility_id"] = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        b["facility_id"] = ObjectId()

    # 3) Normalisation identité
    ident = b["identite"]
    ident["prenom"] = str(ident["prenom"]).strip().capitalize()
    ident["nom"]    = str(ident["nom"]).strip().upper()
    ident["sexe"]   = str(ident["sexe"]).upper()[:1]
    # Date de naissance -> datetime timezone-aware
    if isinstance(ident.get("date_naissance"), str):
        dt = _iso_to_dt(ident["date_naissance"])
        if not dt:
            return {"error": "identite.date_naissance doit être ISO 8601"}, 400
        ident["date_naissance"] = dt
    b["identite"] = ident

    # 4) Timestamps
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    b.setdefault("created_at", now)
    b.setdefault("updated_at", now)
    b.setdefault("deleted", False)

    # 5) Identifiant lisible auto si absent
    if not b.get("identifiant"):
        b["identifiant"] = _gen_patient_ident(current_app.db)

    # 6) Nettoyage None (ex: contacts.absent)
    doc = _strip_none(b)

    # 7) Insertion Mongo
    try:
        ins = current_app.db.patients.insert_one(doc)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201

