from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("patients", __name__)

def _validate_patient(b: dict):
    if "identite" not in b: return "identite is required"
    ident = b["identite"]
    for f in ["prenom", "nom", "date_naissance", "sexe"]:
        if f not in ident: return f"identite.{f} is required"
    return None

@bp.get("")
def list_():
    cur = current_app.db.patients.find({"deleted": {"$ne": True}},
                                       {"identite": 1, "contacts.phone": 1}).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    d = current_app.db.patients.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "not found"}, 404)

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate_patient(b)
    if err: return {"error": err}, 400

    # cast facility_id (optional)
    if b.get("facility_id"):
        try:
            b["facility_id"] = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id must be ObjectId string"}, 400
    else:
        b["facility_id"] = ObjectId()

    # date_naissance string → datetime
    try:
        if isinstance(b["identite"].get("date_naissance"), str):
            b["identite"]["date_naissance"] = datetime.fromisoformat(
                b["identite"]["date_naissance"].replace("Z", "+00:00")
            )
    except Exception:
        return {"error": "identite.date_naissance must be ISO datetime"}, 400

    b.setdefault("created_at", datetime.utcnow())
    b.setdefault("updated_at", datetime.utcnow())
    b.setdefault("deleted", False)

    ins = current_app.db.patients.insert_one(b)
    return {"_id": str(ins.inserted_id)}, 201

@bp.patch("/<id>")
def patch(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400

    b = request.get_json(force=True) or {}
    # convert nested date if provided
    if "identite" in b and isinstance(b.get("identite", {}).get("date_naissance"), str):
        try:
            b["identite"]["date_naissance"] = datetime.fromisoformat(
                b["identite"]["date_naissance"].replace("Z", "+00:00")
            )
        except Exception:
            return {"error": "identite.date_naissance must be ISO datetime"}, 400

    b["updated_at"] = datetime.utcnow()
    r = current_app.db.patients.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    r = current_app.db.patients.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
