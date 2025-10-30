from flask import Blueprint, request, current_app, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone

bp = Blueprint("health_authorities", __name__)  # url_prefix="/api/health_authorities" dans app.py

ALLOWED_REPORT_TYPES = {"case_summary", "disease_reporting", "inventory", "other"}
ALLOWED_STATUS = {"draft", "submitted", "accepted", "rejected"}

def _iso_to_dt(v, field):
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if not isinstance(v, str):
        raise ValueError(f"{field} must be ISO datetime")
    s = v.replace("Z", "+00:00") if v.endswith("Z") else v
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _jsonify(doc):
    """Cast ObjectId/datetime to JSON-safe types."""
    if not doc:
        return doc
    d = dict(doc)
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
        elif isinstance(v, datetime):
            # normalise en UTC + suffixe Z
            v = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            d[k] = v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
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

    now = datetime.utcnow().replace(tzinfo=timezone.utc)
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
    # enlève les champs None
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
        rt = request.args["report_type"]
        if rt not in ALLOWED_REPORT_TYPES:
            return jsonify(error=f"report_type must be one of: {', '.join(sorted(ALLOWED_REPORT_TYPES))}"), 400
        q["report_type"] = rt
    if "status" in request.args:
        st = request.args["status"]
        if st not in ALLOWED_STATUS:
            return jsonify(error=f"status must be one of: {', '.join(sorted(ALLOWED_STATUS))}"), 400
        q["status"] = st

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


