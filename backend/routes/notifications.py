from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

bp = Blueprint("notifications", __name__)

def _validate(b):
    for f in ["channel", "status"]:
        if f not in b:
            return f"{f} is required"
    return None

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate(b)
    if err:
        return {"error": err}, 400

    # Cast optionnels vers ObjectId
    try:
        to_pid = ObjectId(b["to_patient_id"]) if b.get("to_patient_id") else None
        to_did = ObjectId(b["to_doctor_id"])  if b.get("to_doctor_id")  else None
        refid  = ObjectId(b["ref_id"])        if b.get("ref_id")        else None
    except InvalidId:
        return {"error": "invalid id in recipient/ref"}, 400

    # Dates optionnelles
    send_at = None
    if isinstance(b.get("send_at"), str):
        try:
            send_at = datetime.fromisoformat(b["send_at"].replace("Z", "+00:00"))
        except Exception:
            return {"error": "send_at must be ISO8601"}, 400

    doc = {
        "channel": b["channel"],                # sms/email/push
        "status": b.get("status", "queued"),    # queued/sent/failed/read
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False,
    }

    # Ne PAS insérer template=None (provoque la validation 121) :
    if "template" in b and b["template"] is not None:
        doc["template"] = str(b["template"])

    # payload doit être un objet si fourni
    if "payload" in b and b["payload"] is not None:
        if not isinstance(b["payload"], dict):
            return {"error": "payload must be an object"}, 400
        doc["payload"] = b["payload"]

    if to_pid:
        doc["to_patient_id"] = to_pid
    if to_did:
        doc["to_doctor_id"] = to_did
    if refid:
        doc["ref_id"] = refid
    if b.get("ref_type"):
        doc["ref_type"] = b["ref_type"]
    if send_at:
        doc["send_at"] = send_at
    if b.get("sent_at"):
        try:
            doc["sent_at"] = datetime.fromisoformat(b["sent_at"].replace("Z", "+00:00"))
        except Exception:
            return {"error": "sent_at must be ISO8601"}, 400
    if b.get("error") is not None:
        doc["error"] = str(b["error"])

    ins = current_app.db.notifications.insert_one(doc)
    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "to_patient_id" in request.args:
            q["to_patient_id"] = ObjectId(request.args["to_patient_id"])
        if "to_doctor_id" in request.args:
            q["to_doctor_id"] = ObjectId(request.args["to_doctor_id"])
    except InvalidId:
        return {"error": "invalid id"}, 400
    if "status" in request.args:
        q["status"] = request.args["status"]
    if "channel" in request.args:
        q["channel"] = request.args["channel"]

    cur = current_app.db.notifications.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    d = current_app.db.notifications.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "not found"}, 404)

@bp.patch("/<id>")
def patch(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    b = request.get_json(force=True) or {}

    # si on marque "sent", auto-saisir sent_at si absent
    if b.get("status") == "sent" and "sent_at" not in b:
        b["sent_at"] = datetime.utcnow()

    # si payload fourni, vérifier que c'est un objet
    if "payload" in b and b["payload"] is not None and not isinstance(b["payload"], dict):
        return {"error": "payload must be an object"}, 400

    b["updated_at"] = datetime.utcnow()
    r = current_app.db.notifications.update_one({"_id": oid}, {"$set": b})
    return {"matched": r.matched_count, "modified": r.modified_count}, 200

@bp.delete("/<id>")
def soft_delete(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    r = current_app.db.notifications.update_one(
        {"_id": oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}}
    )
    return {"deleted": r.modified_count == 1}, 200
