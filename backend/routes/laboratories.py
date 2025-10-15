from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("laboratories", __name__)

def _validate(b):
    for f in ["patient_id","doctor_id","status"]:
        if f not in b: return f"{f} is required"
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
        return {"error":"invalid id"}, 400

    if not db.patients.find_one({"_id": pid}): return {"error":"patient not found"}, 404
    if not db.doctors.find_one({"_id": did}):  return {"error":"doctor not found"}, 404

    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": ObjectId(b["facility_id"]) if b.get("facility_id") else ObjectId(),
        "status": b.get("status","ordered"),
        "date_ordered": datetime.utcnow(),
        "tests": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }

    if b.get("appointment_id"):
        try:
            doc["appointment_id"] = ObjectId(b["appointment_id"])
        except InvalidId:
            return {"error":"appointment_id must be ObjectId"}, 400

    for t in b.get("tests", []):
        if not isinstance(t, dict): continue
        if not (t.get("code") and t.get("name") and t.get("status")): continue
        nt = {"code": t["code"], "name": t["name"], "status": t["status"]}
        for k in ("result","unit","ref_range","abnormal"):
            if t.get(k) is not None: nt[k] = t.get(k)
        doc["tests"].append(nt)

    if b.get("notes") is not None:
        doc["notes"] = b["notes"]

    ins = db.laboratories.insert_one(doc)
    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "patient_id" in request.args: q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id"  in request.args: q["doctor_id"]  = ObjectId(request.args["doctor_id"])
    except InvalidId:
        return {"error":"invalid id"}, 400
    if "status" in request.args: q["status"] = request.args["status"]

    cur = current_app.db.laboratories.find(q).sort("date_ordered",-1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error":"invalid id"}, 400
    d = current_app.db.laboratories.find_one({"_id": oid})
    return (d, 200) if d else ({"error":"not found"}, 404)

@bp.patch("/<id>")
def patch(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error":"invalid id"}, 400
    b = request.get_json(force=True) or {}
    b["updated_at"] = datetime.utcnow()
    r = current_app.db.laboratories.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error":"invalid id"}, 400
    r = current_app.db.laboratories.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
