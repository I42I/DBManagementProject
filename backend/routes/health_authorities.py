from flask import Blueprint, request, current_app, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("health_authorities", __name__)  # enregistré avec url_prefix="/api/health_authorities" dans app.py

ALLOWED_REPORT_TYPES = {"case_summary", "disease_reporting", "inventory", "other"}
ALLOWED_STATUS = {"draft", "submitted", "accepted", "rejected"}

def _iso_to_dt(v, field):
    if isinstance(v, datetime):
        return v
    if not isinstance(v, str):
        raise ValueError(f"{field} must be ISO datetime")
    return datetime.fromisoformat(v.replace("Z", "+00:00"))

def _jsonify(doc):
    """Cast ObjectId/datetime to str/ISO for safe JSON."""
    if not doc:
        return doc
    d = dict(doc)
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat() + "Z"
    return d

def _validate(b):
    for f in ["report_type", "period_start", "period_end", "status", "facility_id"]:
        if f not in b:
            return f"{f} is required"
    if b.get("report_type") not in ALLOWED_REPORT_TYPES:
        return f"report_type must be one of: {', '.join(sorted(ALLOWED_REPORT_TYPES))}"
    if b.get("status") not in ALLOWED_STATUS:
        return f"status must be one of: {', '.join(sorted(ALLOWED_STATUS))}"
    return None

@bp.post("")
def create():
    b = request.get_json(silent=True) or {}
    err = _validate(b)
    if err:
        return jsonify(error=err), 400

    # IDs
    try:
        facility_id = ObjectId(b["facility_id"])
    except InvalidId:
        return jsonify(error="facility_id must be ObjectId"), 400

    # Dates
    try:
        period_start = _iso_to_dt(b["period_start"], "period_start")
        period_end   = _iso_to_dt(b["period_end"], "period_end")
    except Exception as e:
        return jsonify(error=str(e)), 400

    if period_end < period_start:
        return jsonify(error="period_end must be >= period_start"), 400

    now = datetime.utcnow()
    doc = {
        "facility_id": facility_id,
        "report_type": b["report_type"],
        "period_start": period_start,
        "period_end": period_end,
        "status": b.get("status", "draft"),
        "payload": b.get("payload", {}),
        "external_ref": str(b["external_ref"]) if b.get("external_ref") is not None else None,
        "notes": str(b["notes"]) if b.get("notes") is not None else None,
        "created_at": now,
        "updated_at": now,
        "deleted": False,
    }
    # retire les None pour éviter du bruit
    doc = {k: v for k, v in doc.items() if v is not None}

    if b.get("submitted_at"):
        try:
            doc["submitted_at"] = _iso_to_dt(b["submitted_at"], "submitted_at")
        except Exception as e:
            return jsonify(error=str(e)), 400

    ins = current_app.db.health_authorities.insert_one(doc)
    return jsonify(_id=str(ins.inserted_id)), 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    if "facility_id" in request.args:
        try:
            q["facility_id"] = ObjectId(request.args["facility_id"])
        except InvalidId:
            return jsonify(error="facility_id invalid"), 400
    if "report_type" in request.args:
        q["report_type"] = request.args["report_type"]
    if "status" in request.args:
        q["status"] = request.args["status"]

    cur = current_app.db.health_authorities.find(q).sort("created_at", -1).limit(200)
    return jsonify([_jsonify(d) for d in cur]), 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return jsonify(error="invalid id"), 400
    d = current_app.db.health_authorities.find_one({"_id": oid})
    return (jsonify(_jsonify(d)), 200) if d else (jsonify(error="not found"), 404)

@bp.patch("/<id>")
def patch(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return jsonify(error="invalid id"), 400

    b = request.get_json(silent=True) or {}

    # conversions sûres pour dates statutaires
    if "submitted_at" in b:
        try:
            b["submitted_at"] = _iso_to_dt(b["submitted_at"], "submitted_at")
        except Exception as e:
            return jsonify(error=str(e)), 400
    if "period_start" in b:
        try:
            b["period_start"] = _iso_to_dt(b["period_start"], "period_start")
        except Exception as e:
            return jsonify(error=str(e)), 400
    if "period_end" in b:
        try:
            b["period_end"] = _iso_to_dt(b["period_end"], "period_end")
        except Exception as e:
            return jsonify(error=str(e)), 400
    if b.get("status") == "submitted" and "submitted_at" not in b:
        b["submitted_at"] = datetime.utcnow()

    # interdit de changer _id
    b.pop("_id", None)
    # si facility_id est fourni, valider son format
    if "facility_id" in b:
        try:
            b["facility_id"] = ObjectId(b["facility_id"])
        except InvalidId:
            return jsonify(error="facility_id must be ObjectId"), 400

    b["updated_at"] = datetime.utcnow()
    r = current_app.db.health_authorities.update_one({"_id": oid}, {"$set": b})
    return jsonify(matched=r.matched_count, modified=r.modified_count), 200

@bp.delete("/<id>")
def soft_delete(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return jsonify(error="invalid id"), 400
    r = current_app.db.health_authorities.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return jsonify(deleted=(r.modified_count == 1)), 200
