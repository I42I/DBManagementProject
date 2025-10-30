from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("notifications", __name__)

_ALLOWED_CHANNEL = {"sms", "email", "push"}
_ALLOWED_STATUS  = {"queued", "sent", "failed", "read"}
_ALLOWED_REF     = {"appointment", "consultation", "prescription", "payment", "other"}

def _iso_to_dt(v):
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if not isinstance(v, str):
        return None
    try:
        v = v.replace("Z", "+00:00") if v.endswith("Z") else v
        dt = datetime.fromisoformat(v)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def _cast_oid(v):
    if v is None or isinstance(v, ObjectId):
        return v
    try:
        return ObjectId(v)
    except InvalidId:
        return None

def _validate(b):
    for f in ("channel", "status"):
        if f not in b:
            return f"{f} requis"
    if b["channel"] not in _ALLOWED_CHANNEL:
        return "channel invalide (sms|email|push)"
    if b["status"] not in _ALLOWED_STATUS:
        return "status invalide (queued|sent|failed|read)"
    if "ref_type" in b and b["ref_type"] not in _ALLOWED_REF:
        return "ref_type invalide (appointment|consultation|prescription|payment|other)"
    if "payload" in b and b["payload"] is not None and not isinstance(b["payload"], dict):
        return "payload doit être un objet"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err:
        return {"error": err}, 400

    # cast ObjectId facultatifs
    to_pid = _cast_oid(b.get("to_patient_id"))
    if b.get("to_patient_id") is not None and to_pid is None:
        return {"error": "to_patient_id doit être un ObjectId"}, 400

    to_did = _cast_oid(b.get("to_doctor_id"))
    if b.get("to_doctor_id") is not None and to_did is None:
        return {"error": "to_doctor_id doit être un ObjectId"}, 400

    ref_id = _cast_oid(b.get("ref_id"))
    if b.get("ref_id") is not None and ref_id is None:
        return {"error": "ref_id doit être un ObjectId"}, 400

    # dates facultatives
    send_at    = _iso_to_dt(b.get("send_at"))    if b.get("send_at")    else None
    sent_at    = _iso_to_dt(b.get("sent_at"))    if b.get("sent_at")    else None
    expires_at = _iso_to_dt(b.get("expires_at")) if b.get("expires_at") else None
    if b.get("send_at") and not send_at:
        return {"error": "send_at doit être ISO 8601"}, 400
    if b.get("sent_at") and not sent_at:
        return {"error": "sent_at doit être ISO 8601"}, 400
    if b.get("expires_at") and not expires_at:
        return {"error": "expires_at doit être ISO 8601"}, 400

    # si status=sent sans sent_at -> on le pose à maintenant
    if b.get("status") == "sent" and not sent_at:
        sent_at = datetime.utcnow()

    doc = {
        "channel": b["channel"],         # sms/email/push
        "status":  b["status"],          # queued/sent/failed/read
        "template": b.get("template"),
        "payload":  b.get("payload") if isinstance(b.get("payload"), dict) else None,
        "ref_type": b.get("ref_type"),
        "ref_id":   ref_id,
        "to_patient_id": to_pid,
        "to_doctor_id":  to_did,
        "send_at":    send_at,
        "sent_at":    sent_at,
        "expires_at": expires_at,        # utilisé par le TTL index
        "error": b.get("error"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False,
    }
    # retire les clés à None pour rester propre
    doc = {k: v for k, v in doc.items() if v is not None}

    try:
        ins = current_app.db.notifications.insert_one(doc)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    # filtres simples
    if "status" in request.args:
        q["status"] = request.args["status"]
    if "channel" in request.args:
        q["channel"] = request.args["channel"]
    if "ref_type" in request.args:
        q["ref_type"] = request.args["ref_type"]

    for arg, key in (("to_patient_id", "to_patient_id"), ("to_doctor_id", "to_doctor_id")):
        if arg in request.args:
            oid = _cast_oid(request.args[arg])
            if oid is None:
                return {"error": f"{arg} invalide"}, 400
            q[key] = oid

    cur = current_app.db.notifications.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    oid = _cast_oid(id)
    if oid is None:
        return {"error": "id invalide"}, 400
    d = current_app.db.notifications.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

