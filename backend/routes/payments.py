from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("payments", __name__)

def _validate(b):
    for f in ["patient_id","amount","currency","status"]:
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
    except InvalidId:
        return {"error":"invalid patient_id"}, 400
    if not db.patients.find_one({"_id": pid}): return {"error":"patient not found"}, 404

    try:
        appt_id = ObjectId(b["appointment_id"])   if b.get("appointment_id")   else None
        consult_id = ObjectId(b["consultation_id"]) if b.get("consultation_id") else None
        facility_id = ObjectId(b["facility_id"])  if b.get("facility_id") else ObjectId()
    except InvalidId:
        return {"error":"invalid id in optional refs"}, 400

    due_date = datetime.fromisoformat(b["due_date"].replace("Z","+00:00")) if isinstance(b.get("due_date"), str) else None
    paid_at  = datetime.fromisoformat(b["paid_at"].replace("Z","+00:00"))  if isinstance(b.get("paid_at"), str)  else None

    doc = {
        "patient_id": pid,
        "facility_id": facility_id,
        "amount": b["amount"],
        "currency": b["currency"],
        "method": b.get("method","cash"),
        "status": b.get("status","pending"),
        "items": b.get("items", []),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }
    if appt_id:   doc["appointment_id"] = appt_id
    if consult_id:doc["consultation_id"] = consult_id
    if b.get("invoice_no") is not None: doc["invoice_no"] = b["invoice_no"]
    if due_date:  doc["due_date"] = due_date
    if paid_at:   doc["paid_at"] = paid_at

    ins = db.payments.insert_one(doc)
    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    if "patient_id" in request.args:
        try: q["patient_id"] = ObjectId(request.args["patient_id"])
        except InvalidId: return {"error":"invalid id"}, 400
    if "status" in request.args: q["status"] = request.args["status"]

    cur = current_app.db.payments.find(q).sort("created_at",-1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error":"invalid id"}, 400
    d = current_app.db.payments.find_one({"_id": oid})
    return (d, 200) if d else ({"error":"not found"}, 404)

@bp.patch("/<id>")
def patch(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error":"invalid id"}, 400
    b = request.get_json(force=True) or {}
    if b.get("status") == "paid" and "paid_at" not in b:
        b["paid_at"] = datetime.utcnow()
    b["updated_at"] = datetime.utcnow()
    r = current_app.db.payments.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error":"invalid id"}, 400
    r = current_app.db.payments.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
