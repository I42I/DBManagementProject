# ===========================================================
#  pharmacies.py — Gestion des délivrances en pharmacie
#  Rôle:
#
#  Endpoints:
#    POST /api/pharmacies        -> créer un enregistrement de délivrance
#    GET  /api/pharmacies        -> lister (filtres)
#    GET  /api/pharmacies/<id>   -> détail
#
#  Points clés :
#    - Validation stricte (status, items[], cast des ObjectId…)
#    - Conversion ISO8601 → datetime UTC (dispensed_at)
#    - Nettoyage des None pour respecter le $jsonSchema
#    - facility_id généré si absent (conforme à tes schémas)
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone
from utils import strip_none, iso_to_dt, validate_objectid, check_exists


bp = Blueprint("pharmacies", __name__)

_ALLOWED_STATUS = {"requested", "prepared", "dispensed", "cancelled"}

# -------------------------------
# Helpers
# -------------------------------
def _validate_create(b: dict):
    """
    Contrôles fonctionnels d’entrée.
    Requis: patient_id, doctor_id, items[], status.
    Chaque item doit au minimum contenir { dci, qty }.
    """
    for f in ("patient_id", "doctor_id", "items", "status"):
        if f not in b:
            return f"{f} requis"

    if b["status"] not in _ALLOWED_STATUS:
        return "status invalide (requested|prepared|dispensed|cancelled)"

    if not isinstance(b["items"], list) or len(b["items"]) == 0:
        return "items doit être un tableau non vide"

    for it in b["items"]:
        if not isinstance(it, dict):
            return "chaque item doit être un objet"
        if not it.get("dci"):
            return "chaque item doit contenir dci"
        # accepter qty ou quantity ; doit être numérique
        q = it.get("qty", it.get("quantity"))
        if q is None:
            return "chaque item doit contenir qty"
        if not isinstance(q, (int, float, str)):
            return "qty doit être numérique"
        # si string, on vérifiera/castera plus bas
    return None

def _normalize_items(items_in):
    """
    Normalise chaque item :
      in : { dci, qty|quantity, brand?, forme?, posologie?, notes? }
      out: { dci, qty (float/int), brand?, forme?, posologie?, notes? }
    """
    out = []
    for it in items_in:
        if not isinstance(it, dict):
            continue
        q = it.get("qty", it.get("quantity"))
        # cast léger si string numérique
        if isinstance(q, str):
            try:
                q = float(q) if (("." in q) or ("e" in q.lower())) else int(q)
            except Exception:
                continue  # qty invalide -> on jette l’item
        if not isinstance(q, (int, float)):
            continue
        item = {
            "dci": it.get("dci"),
            "qty": q,
        }
        # champs optionnels propres
        if it.get("brand") is not None:     item["brand"] = it["brand"]
        if it.get("forme") is not None:     item["forme"] = it["forme"]
        if it.get("posologie") is not None: item["posologie"] = it["posologie"]
        if it.get("notes") is not None:     item["notes"] = it["notes"]

        if item.get("dci"):
            out.append(item)
    return out

# -------------------------------
# POST /api/pharmacies — création
# -------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # 1) Validation fonctionnelle
    err = _validate_create(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # 2) Cast + existence patient/doctor
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    if not db.patients.find_one({"_id": pid}, {"_id": 1}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}, {"_id": 1}):
        return {"error": "médecin introuvable"}, 404

    # 3) prescription_id optionnel + existence
    pres_id = None
    if b.get("prescription_id"):
        try:
            pres_id = ObjectId(b["prescription_id"])
        except InvalidId:
            return {"error": "prescription_id doit être un ObjectId"}, 400
        if not db.prescriptions.find_one({"_id": pres_id}, {"_id": 1}):
            return {"error": "prescription introuvable"}, 404

    # 4) facility_id (requis par schéma) : généré si absent
    if b.get("facility_id"):
        try:
            facility_id = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        facility_id = ObjectId()

    # 5) Normalisation items
    items = _normalize_items(b["items"])
    if not items:
        return {"error": "items invalides (dci+qty requis)"}, 400

    # 6) Date optionnelle : dispensed_at (ISO)
    dispensed_at = None
    if b.get("dispensed_at"):
        dispensed_at = iso_to_dt(b["dispensed_at"])
        if not dispensed_at:
            return {"error": "dispensed_at doit être ISO 8601"}, 400

    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    # 7) Document Mongo — on nettoie les None
    doc = strip_none({
        "patient_id":  pid,
        "doctor_id":   did,
        "facility_id": facility_id,
        "prescription_id": pres_id,
        "status": b.get("status", "requested"),
        "items": items,
        "dispensed_at": dispensed_at,
        "created_at": now,
        "updated_at": now,
        "deleted": False,
    })

    # 8) Insertion
    try:
        ins = db.pharmacies.insert_one(doc)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201

# -------------------------------
# GET /api/pharmacies — liste
# -------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres ids
    try:
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id" in request.args:
            q["doctor_id"] = ObjectId(request.args["doctor_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
        if "prescription_id" in request.args:
            q["prescription_id"] = ObjectId(request.args["prescription_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    # Filtre status simple
    if "status" in request.args:
        q["status"] = request.args["status"]

    cur = current_app.db.pharmacies.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

# -------------------------------
# GET /api/pharmacies/<id> — détail
# -------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.pharmacies.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

