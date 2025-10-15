from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("health_authorities", __name__)

def _validate(b):
    for f in ["report_type","period_start","period_end","status","facility_id"]:
        if f not in b: return f"{f} is required"
    # validate allowed report_type enum to surface clear error to client
    allowed = {"case_summary","disease_reporting","inventory","other"}
    if b.get("report_type") not in allowed:
        return f"report_type must be one of: {','.join(sorted(allowed))}"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err: return {"error": err}, 400

    try:
        facility_id = ObjectId(b["facility_id"])
    except InvalidId:
        return {"error": "facility_id must be ObjectId"}, 400

    try:
        period_start = datetime.fromisoformat(b["period_start"].replace("Z", "+00:00"))
        period_end   = datetime.fromisoformat(b["period_end"].replace("Z", "+00:00"))
    except Exception:
        return {"error": "period_start/period_end must be ISO datetimes"}, 400

    doc = {
        "facility_id": facility_id,
        "report_type": b["report_type"],
        "period_start": period_start,
        "period_end": period_end,
        "status": b.get("status", "draft"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }

    if b.get("submitted_at"):
        try:
            doc["submitted_at"] = datetime.fromisoformat(b["submitted_at"].replace("Z","+00:00"))
        except Exception:
            return {"error": "submitted_at must be ISO datetime"}, 400

    if b.get("external_ref") is not None: doc["external_ref"] = str(b["external_ref"])
    if b.get("notes") is not None:        doc["notes"] = str(b["notes"])
    if b.get("payload") is not None:      doc["payload"] = b["payload"]

    ins = current_app.db.health_authorities.insert_one(doc)
    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    if "facility_id" in request.args:
        try: q["facility_id"] = ObjectId(request.args["facility_id"])
        except InvalidId: return {"error": "facility_id invalid"}, 400
    if "report_type" in request.args: q["report_type"] = request.args["report_type"]
    if "status" in request.args:      q["status"]      = request.args["status"]

    cur = current_app.db.health_authorities.find(q).sort("created_at",-1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error":"invalid id"}, 400
    d = current_app.db.health_authorities.find_one({"_id": oid})
    return (d, 200) if d else ({"error":"not found"}, 404)

@bp.patch("/<id>")
def patch(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error":"invalid id"}, 400
    b = request.get_json(force=True) or {}
    if b.get("status") == "submitted" and "submitted_at" not in b:
        b["submitted_at"] = datetime.utcnow()
    b["updated_at"] = datetime.utcnow()
    r = current_app.db.health_authorities.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try: oid = ObjectId(id)
    except InvalidId: return {"error":"invalid id"}, 400
    r = current_app.db.health_authorities.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
