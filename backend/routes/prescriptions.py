from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime

bp = Blueprint("prescriptions", __name__)

def _validate_create(b: dict):
    for f in ("patient_id", "doctor_id", "consultation_id", "items"):
        if f not in b:
            return f"{f} requis"
    if not isinstance(b["items"], list) or len(b["items"]) == 0:
        return "items doit être un tableau non vide"
    # chaque item: dci + posologie requis (conforme $jsonSchema)
    for it in b["items"]:
        if not isinstance(it, dict):
            return "chaque item doit être un objet"
        if "dci" not in it:
            return "chaque item doit contenir dci"
        if "posologie" not in it:
            return "chaque item doit contenir posologie"
    return None

def _normalize_items(items_in):
    """Conserve uniquement les champs autorisés et enlève les None."""
    out = []
    for it in items_in:
        item = {
            "dci": it.get("dci"),
            "forme": it.get("forme"),
            "posologie": it.get("posologie"),
            "duree_j": it.get("duree_j"),
            "contre_indications": it.get("contre_indications"),
        }
        item = {k: v for k, v in item.items() if v is not None}
        out.append(item)
    return out

def _strip_none(d: dict):
    """Supprime les paires clé: None au premier niveau (pratique pour PATCH)."""
    return {k: v for k, v in d.items() if v is not None}

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate_create(b)
    if err:
        return {"error": err}, 400

    db = current_app.db
    # cast ids
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
        cid = ObjectId(b["consultation_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id/consultation_id doivent être des ObjectId"}, 400

    # existence de base
    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404
    if not db.consultations.find_one({"_id": cid}):
        return {"error": "consultation introuvable"}, 404

    # facility_id optionnel (non requis par ton schema)
    fid = None
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400

    items = _normalize_items(b["items"])

    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "consultation_id": cid,
        "items": items,
        "renouvellements": b.get("renouvellements", 0),
        "notes": b.get("notes"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }
    if fid:
        doc["facility_id"] = fid
    # retire None éventuels (notes si absente, etc.)
    doc = _strip_none(doc)

    try:
        ins = db.prescriptions.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return {"error": "validation_mongo", "details": details}, 400

    return {"_id": str(ins.inserted_id)}, 201

@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}
    try:
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id" in request.args:
            q["doctor_id"] = ObjectId(request.args["doctor_id"])
        if "consultation_id" in request.args:
            q["consultation_id"] = ObjectId(request.args["consultation_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    cur = current_app.db.prescriptions.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.prescriptions.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)


