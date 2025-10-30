from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime

bp = Blueprint("patients", __name__)

_ALLOWED_SEX = {"M", "F", "X"}

def _validate_patient(b: dict):
    if "identite" not in b:
        return "identite requis"
    ident = b["identite"]
    for f in ("prenom", "nom", "date_naissance", "sexe"):
        if f not in ident:
            return f"identite.{f} requis"
    if ident.get("sexe") not in _ALLOWED_SEX:
        return "identite.sexe doit être M, F ou X"
    return None

@bp.get("")
def list_():
    cur = current_app.db.patients.find(
        {"deleted": {"$ne": True}},
        {"identite": 1, "contacts.phone": 1}
    ).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.patients.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate_patient(b)
    if err:
        return {"error": err}, 400

    # facility_id requis par le $jsonSchema → générer si absent
    if b.get("facility_id"):
        try:
            b["facility_id"] = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        b["facility_id"] = ObjectId()

    # identite.date_naissance (ISO 8601 -> datetime)
    try:
        if isinstance(b["identite"].get("date_naissance"), str):
            b["identite"]["date_naissance"] = datetime.fromisoformat(
                b["identite"]["date_naissance"].replace("Z", "+00:00")
            )
    except Exception:
        return {"error": "identite.date_naissance doit être ISO 8601"}, 400

    b.setdefault("created_at", datetime.utcnow())
    b.setdefault("updated_at", datetime.utcnow())
    b.setdefault("deleted", False)

    try:
        ins = current_app.db.patients.insert_one(b)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201


