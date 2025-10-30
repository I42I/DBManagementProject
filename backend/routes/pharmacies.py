from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime

bp = Blueprint("pharmacies", __name__)

_ALLOWED_STATUS = {"requested", "prepared", "dispensed", "cancelled"}

def _validate_create(b: dict):
    # champs requis côté API
    for f in ("patient_id", "doctor_id", "items", "status"):
        if f not in b:
            return f"{f} requis"
    if b["status"] not in _ALLOWED_STATUS:
        return "status invalide (requested|prepared|dispensed|cancelled)"
    if not isinstance(b["items"], list) or len(b["items"]) == 0:
        return "items doit être un tableau non vide"
    # valider chaque item (conforme au validator: dci + qty requis)
    for it in b["items"]:
        if not isinstance(it, dict):
            return "chaque item doit être un objet"
        if not it.get("dci"):
            return "chaque item doit contenir dci"
        # accepter qty ou quantity → on mappe vers qty
        q = it.get("qty", it.get("quantity", None))
        if q is None:
            return "chaque item doit contenir qty"
        if not isinstance(q, (int, float)):
            return "qty doit être numérique"
    return None

def _normalize_items(items_in):
    """Retourne une liste d'items propre: {dci, brand?, forme?, posologie?, qty, notes?}"""
    out = []
    for it in items_in:
        if not isinstance(it, dict):
            continue
        q = it.get("qty", it.get("quantity", None))
        if q is None:
            continue
        try:
            # cast léger si string numérique
            if isinstance(q, str):
                q = float(q) if (("." in q) or ("e" in q.lower())) else int(q)
        except Exception:
            continue
        item = {"dci": it.get("dci"), "qty": q}
        if it.get("brand") is not None:     item["brand"] = it["brand"]
        if it.get("forme") is not None:     item["forme"] = it["forme"]
        if it.get("posologie") is not None: item["posologie"] = it["posologie"]
        if it.get("notes") is not None:     item["notes"] = it["notes"]
        if item.get("dci"):  # on garde seulement si dci présent
            out.append(item)
    return out

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    err = _validate_create(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # cast et existence patient/doctor
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # prescription_id optionnel + existence
    pres_id = None
    if b.get("prescription_id"):
        try:
            pres_id = ObjectId(b["prescription_id"])
        except InvalidId:
            return {"error": "prescription_id doit être un ObjectId"}, 400
        if not db.prescriptions.find_one({"_id": pres_id}):
            return {"error": "prescription introuvable"}, 404

    # facility_id requis par le $jsonSchema → générer si absent
    if b.get("facility_id"):
        try:
            facility_id = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        facility_id = ObjectId()

    items = _normalize_items(b["items"])
    if not items:
        return {"error": "items invalides (dci+qty requis)"}, 400

    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": facility_id,
        "status": b.get("status", "requested"),
        "items": items,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted": False
    }
    if pres_id:
        doc["prescription_id"] = pres_id

    # dispensed_at optionnel (ISO8601)
    if b.get("dispensed_at"):
        try:
            doc["dispensed_at"] = datetime.fromisoformat(b["dispensed_at"].replace("Z", "+00:00"))
        except Exception:
            return {"error": "dispensed_at doit être ISO 8601"}, 400

    try:
        ins = db.pharmacies.insert_one(doc)
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
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400
    if "status" in request.args:
        q["status"] = request.args["status"]

    cur = current_app.db.pharmacies.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.pharmacies.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)


