from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("pharmacies", __name__)

def _validate(b):
    for f in ["patient_id","doctor_id","items","status"]:
        if f not in b: return f"{f} is required"
    if not isinstance(b["items"], list) or not b["items"]:
        return "items must be non-empty array"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err: return {"error": err}, 400

    db = current_app.db
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id must be ObjectId"}, 400

    if not db.patients.find_one({"_id": pid}): return {"error":"patient not found"}, 404
    if not db.doctors.find_one({"_id": did}):  return {"error":"doctor not found"}, 404

    pres_id = None
    if b.get("prescription_id"):
        try:
            pres_id = ObjectId(b["prescription_id"])
        except InvalidId:
            return {"error": "prescription_id must be ObjectId"}, 400
        if not db.prescriptions.find_one({"_id": pres_id}):
            return {"error":"prescription not found"}, 404

    facility_id = ObjectId(b["facility_id"]) if b.get("facility_id") else ObjectId()

    items = []
    for it in b.get("items", []):
        if not isinstance(it, dict): continue
        ni = {}
        if it.get("dci"):       ni["dci"] = it["dci"]
        if it.get("brand"):     ni["brand"] = it["brand"]
        if it.get("posologie"): ni["posologie"] = it["posologie"]
        if it.get("qty") is not None:       ni["qty"] = it["qty"]
        if it.get("quantity") is not None and "qty" not in ni:
            ni["qty"] = it["quantity"]
        if ni.get("dci") or ni.get("brand"):
            items.append(ni)

    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": facility_id,
        "status": b.get("status","requested"),
        "items": items,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }
    if pres_id: doc["prescription_id"] = pres_id
    if b.get("dispensed_at"):
        try:
            doc["dispensed_at"] = datetime.fromisoformat(b["dispensed_at"].replace("Z","+00:00"))
        except Exception:
            return {"error": "dispensed_at must be ISO datetime"}, 400

    ins = db.pharmacies.insert_one(doc)
    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    if "patient_id" in request.args:
        try: q["patient_id"] = ObjectId(request.args["patient_id"])
        except InvalidId: return {"error": "patient_id invalid"}, 400
    if "doctor_id" in request.args:
        try: q["doctor_id"] = ObjectId(request.args["doctor_id"])
        except InvalidId: return {"error": "doctor_id invalid"}, 400
    if "status" in request.args: q["status"] = request.args["status"]

    cur = current_app.db.pharmacies.find(q).sort("created_at",-1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error": "invalid id"}, 400
    d = current_app.db.pharmacies.find_one({"_id": oid})
    return (d, 200) if d else ({"error":"not found"}, 404)

@bp.patch("/<id>")
def patch(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error": "invalid id"}, 400
    b = request.get_json(force=True) or {}
    if b.get("status") == "dispensed" and "dispensed_at" not in b:
        b["dispensed_at"] = datetime.utcnow()
    b["updated_at"] = datetime.utcnow()
    r = current_app.db.pharmacies.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error": "invalid id"}, 400
    r = current_app.db.pharmacies.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
