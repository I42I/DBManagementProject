# ===========================================================
#  doctors.py — Gestion des médecins (doctors collection)
# 
#
#  Endpoints:
#    POST /api/doctors        -> créer un médecin
#    GET  /api/doctors        -> lister (filtres)
#    GET  /api/doctors/<id>   -> détail
#
#  Points clés :
#    - Validation stricte de identite.prenom / nom et specialites
#    - facility_id généré si absent (cohérent avec les autres modèles)
#    - Nettoyage et normalisation des chaînes (trim, non vide)
#    - Timestamps en UTC
# ===========================================================

from flask import Blueprint, request, current_app, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone
from utils import strip_none, iso_to_dt, validate_objectid

bp = Blueprint("doctors", __name__)


# -------------------------------
# Validation d'entrée
# -------------------------------
def _validate_create(b: dict):
    """Valide les champs requis à la création d’un médecin."""
    if "identite" not in b:
        return "identite requis"

    ident = b["identite"]
    for f in ("prenom", "nom"):
        if f not in ident:
            return f"identite.{f} requis"
        if not isinstance(ident[f], str) or not ident[f].strip():
            return f"identite.{f} doit être une chaîne non vide"

    sp = b.get("specialites")
    if not isinstance(sp, list) or len(sp) == 0:
        return "specialites doit être un tableau non vide"
    if not all(isinstance(x, str) and x.strip() for x in sp):
        return "specialites doit contenir des chaînes non vides"

    return None

# -------------------------------
# GET /api/doctors — liste
# -------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtre par spécialité (ex: ?specialite=Cardiologue)
    spec = request.args.get("specialite")
    if spec:
        q["specialites"] = spec.strip()

    # Filtre par facility_id
    if "facility_id" in request.args:
        try:
            q["facility_id"] = ObjectId(request.args["facility_id"])
        except InvalidId:
            return jsonify(error="facility_id invalide"), 400

    cur = current_app.db.doctors.find(
        q, {"identite": 1, "specialites": 1, "facility_id": 1}
    ).sort("created_at", -1).limit(200)

    return jsonify([
        {
            "_id": str(d["_id"]),
            "identite": d.get("identite", {}),
            "specialites": d.get("specialites", []),
            "facility_id": str(d["facility_id"]) if d.get("facility_id") else None
        }
        for d in cur
    ]), 200

# -------------------------------
# GET /api/doctors/<id> — détail
# -------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return jsonify(error="id invalide"), 400

    d = current_app.db.doctors.find_one({"_id": oid})
    if not d:
        return jsonify(error="introuvable"), 404

    # Conversion JSON-safe
    d["_id"] = str(d["_id"])
    if "facility_id" in d and isinstance(d["facility_id"], ObjectId):
        d["facility_id"] = str(d["facility_id"])

    return jsonify(d), 200

# -------------------------------
# POST /api/doctors — création
# -------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # Validation fonctionnelle
    err = _validate_create(b)
    if err:
        return jsonify(error=err), 400

    # Cast facility_id ou génération
    if b.get("facility_id"):
        try:
            b["facility_id"] = ObjectId(b["facility_id"])
        except InvalidId:
            return jsonify(error="facility_id doit être un ObjectId"), 400
    else:
        b["facility_id"] = ObjectId()  # génération automatique (mock facility)

    # Normalisation des chaînes
    b["identite"]["prenom"] = b["identite"]["prenom"].strip().capitalize()
    b["identite"]["nom"] = b["identite"]["nom"].strip().upper()
    b["specialites"] = [s.strip() for s in b["specialites"]]

    # Timestamps UTC
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    b["created_at"] = now
    b["updated_at"] = now
    b["deleted"] = False

    # Nettoyage des None
    doc = strip_none(b)

    # Insertion Mongo
    try:
        ins = current_app.db.doctors.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return jsonify(error="validation_mongo", details=details), 400

    return jsonify(_id=str(ins.inserted_id)), 201
