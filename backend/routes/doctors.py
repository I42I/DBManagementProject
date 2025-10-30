from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime

bp = Blueprint("doctors", __name__)

def _validate_create(b: dict):
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

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    # (optionnel) filtres simples
    spec = request.args.get("specialite")
    if spec:
        q["specialites"] = spec
    if "facility_id" in request.args:
        try:
            q["facility_id"] = ObjectId(request.args["facility_id"])
        except InvalidId:
            return {"error": "facility_id invalide"}, 400

    cur = current_app.db.doctors.find(q, {"identite": 1, "specialites": 1}).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.doctors.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate_create(b)
    if err:
        return {"error": err}, 400

    # facility_id requis par le schéma → générer si absent
    if b.get("facility_id"):
        try:
            b["facility_id"] = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        b["facility_id"] = ObjectId()

    # normaliser strings
    b["identite"]["prenom"] = b["identite"]["prenom"].strip()
    b["identite"]["nom"] = b["identite"]["nom"].strip()
    b["specialites"] = [s.strip() for s in b["specialites"]]

    b.setdefault("created_at", datetime.utcnow())
    b.setdefault("updated_at", datetime.utcnow())
    b.setdefault("deleted", False)

    try:
        ins = current_app.db.doctors.insert_one(b)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201
