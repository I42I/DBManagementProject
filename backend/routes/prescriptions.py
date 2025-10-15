from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("prescriptions", __name__)

def _validate(b):
    for f in ["patient_id","doctor_id","consultation_id","items"]:
        if f not in b: return f"{f} is required"
    if not isinstance(b["items"], list) or not b["items"]:
        return "items must be a non-empty array"
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
        cid = ObjectId(b["consultation_id"])
    except InvalidId:
        return {"error":"invalid id"}, 400

    if not db.patients.find_one({"_id": pid}):      return {"error":"patient not found"}, 404
    if not db.doctors.find_one({"_id": did}):       return {"error":"doctor not found"}, 404
    if not db.consultations.find_one({"_id": cid}): return {"error":"consultation not found"}, 404

    items = []
    for it in b.get("items", []):
        if not isinstance(it, dict): continue
        item = {}
        if it.get("dci") is not None:        item["dci"] = it["dci"]
        if it.get("posologie") is not None:  item["posologie"] = it["posologie"]
        if "quantity" in it and it.get("quantity") is not None:
            item["quantity"] = it["quantity"]
        if "qty" in it and it.get("qty") is not None and "quantity" not in item:
            item["quantity"] = it["qty"]
        if item: items.append(item)

    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "consultation_id": cid,
        "items": items,
        "renouvellements": b.get("renouvellements", 0),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }
    if b.get("notes") is not None:
        doc["notes"] = b["notes"]

    ins = db.prescriptions.insert_one(doc)
    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "patient_id" in request.args: q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id"  in request.args: q["doctor_id"]  = ObjectId(request.args["doctor_id"])
    except InvalidId:
        return {"error":"invalid id"}, 400
    cur = current_app.db.prescriptions.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error":"invalid id"}, 400
    d = current_app.db.prescriptions.find_one({"_id": oid})
    return (d, 200) if d else ({"error":"not found"}, 404)

@bp.patch("/<id>")
def patch(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error":"invalid id"}, 400

    b = request.get_json(force=True) or {}

    # Optionnel: garder une validation légère des items si fournis
    if "items" in b:
        items = []
        for it in b.get("items", []):
            if not isinstance(it, dict): 
                continue
            item = {}
            if it.get("dci") is not None:
                item["dci"] = it["dci"]
            if it.get("posologie") is not None:
                item["posologie"] = it["posologie"]
            if "quantity" in it and it.get("quantity") is not None:
                item["quantity"] = it["quantity"]
            if "qty" in it and it.get("qty") is not None and "quantity" not in item:
                item["quantity"] = it["qty"]
            if item:
                items.append(item)
        b["items"] = items

    b["updated_at"] = datetime.utcnow()
    r = current_app.db.prescriptions.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200


@bp.delete("/<id>")
def soft_delete(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error":"invalid id"}, 400
    r = current_app.db.prescriptions.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
