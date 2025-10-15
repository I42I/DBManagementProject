from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("doctors", __name__)

def _validate(b):
    if "identite" not in b: return "identite is required"
    if "specialites" not in b or not isinstance(b["specialites"], list) or not b["specialites"]:
        return "specialites (non-empty array) is required"
    return None

@bp.get("")
def list_():
    cur = current_app.db.doctors.find({"deleted": {"$ne": True}},
                                      {"identite": 1, "specialites": 1}).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    d = current_app.db.doctors.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "not found"}, 404)

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err: return {"error": err}, 400
    # If facility_id is provided but null, treat as not provided
    if "facility_id" in b and (b.get("facility_id") is not None and b.get("facility_id") != ""):
        try:
            b["facility_id"] = ObjectId(b["facility_id"]) if not isinstance(b["facility_id"], ObjectId) else b["facility_id"]
        except Exception:
            return {"error": "facility_id must be a valid ObjectId if provided"}, 400
    else:
        b["facility_id"] = ObjectId()
    b.setdefault("created_at", datetime.utcnow())
    b.setdefault("updated_at", datetime.utcnow())
    b.setdefault("deleted", False)
    ins = current_app.db.doctors.insert_one(b)
    return {"_id": str(ins.inserted_id)}, 201

@bp.patch("/<id>")
def patch(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    b = request.get_json(force=True) or {}
    b["updated_at"] = datetime.utcnow()
    r = current_app.db.doctors.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    r = current_app.db.doctors.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
