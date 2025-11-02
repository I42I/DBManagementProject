# ===========================================================
#  payments.py — Gestion des paiements
#  
#  Rôle :
#    - Enregistrer un paiement (liée à un patient, consultation, etc.)
#    - Lister les paiements (filtrables par status, method, etc.)
#    - Consulter un paiement précis
#  Points clés :
#    - Validation stricte des types et valeurs autorisées
#    - Conversion ISO8601 → datetime UTC
#    - Nettoyage des None avant insertion (compatibilité validator Mongo)
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("payments", __name__)

# -----------------------------------------------------------
# Énumérations autorisées (valeurs conformes au $jsonSchema)
# -----------------------------------------------------------
_ALLOWED_CURRENCY = {"XAF", "XOF", "EUR", "USD"}
_ALLOWED_METHOD   = {"cash", "card", "mobile", "insurance"}
_ALLOWED_STATUS   = {"pending", "paid", "failed", "refunded", "cancelled"}
_ALLOWED_ITEM_REF = {"appointment", "consultation", "laboratory", "pharmacy", "other"}


# -----------------------------------------------------------
# Outils : conversions et nettoyage
# -----------------------------------------------------------
def _iso_to_dt(s: str):
    """Convertit une chaîne ISO8601 en datetime UTC."""
    try:
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _strip_none(d: dict):
    """Supprime les clés dont la valeur est None (évite null dans Mongo)."""
    return {k: v for k, v in d.items() if v is not None}


# -----------------------------------------------------------
# Validation du corps JSON pour POST /api/payments
# -----------------------------------------------------------
def _validate(b):
    # Champs requis
    for f in ("patient_id", "amount", "currency", "status"):
        if f not in b:
            return f"{f} requis"

    # Montant
    if not isinstance(b["amount"], (int, float)) or b["amount"] < 0:
        return "amount doit être numérique ≥ 0"

    # Devise
    if b["currency"] not in _ALLOWED_CURRENCY:
        return f"currency invalide ({'|'.join(_ALLOWED_CURRENCY)})"

    # Méthode de paiement
    if "method" in b and b["method"] not in _ALLOWED_METHOD:
        return f"method invalide ({'|'.join(_ALLOWED_METHOD)})"

    # Statut
    if b["status"] not in _ALLOWED_STATUS:
        return f"status invalide ({'|'.join(_ALLOWED_STATUS)})"

    # Items optionnels
    if "items" in b:
        if not isinstance(b["items"], list):
            return "items doit être un tableau"
        for it in b["items"]:
            if not isinstance(it, dict):
                return "chaque item doit être un objet"
            if "ref_type" in it and it["ref_type"] not in _ALLOWED_ITEM_REF:
                return f"items.ref_type invalide ({'|'.join(_ALLOWED_ITEM_REF)})"
            if "ref_id" in it and not isinstance(it["ref_id"], (str, ObjectId)):
                return "items.ref_id doit être un ObjectId (ou chaîne)"
            if "amount" in it and not isinstance(it["amount"], (int, float)):
                return "items.amount doit être numérique"

    return None


# -----------------------------------------------------------
# POST /api/payments — création d’un paiement
# -----------------------------------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    #  validation
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    #  patient_id obligatoire
    try:
        pid = ObjectId(b["patient_id"])
    except InvalidId:
        return {"error": "patient_id doit être un ObjectId"}, 400
    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404

    # références optionnelles
    try:
        appt_id    = ObjectId(b["appointment_id"])   if b.get("appointment_id")   else None
        consult_id = ObjectId(b["consultation_id"])  if b.get("consultation_id")  else None
        fid        = ObjectId(b["facility_id"])      if b.get("facility_id")      else ObjectId()
    except InvalidId:
        return {"error": "références optionnelles: ObjectId invalide"}, 400

    # dates optionnelles
    due_date = _iso_to_dt(b["due_date"]) if isinstance(b.get("due_date"), str) else None
    if isinstance(b.get("due_date"), str) and not due_date:
        return {"error": "due_date doit être au format ISO 8601"}, 400

    paid_at = _iso_to_dt(b["paid_at"]) if isinstance(b.get("paid_at"), str) else None
    if isinstance(b.get("paid_at"), str) and not paid_at:
        return {"error": "paid_at doit être au format ISO 8601"}, 400

    #  normalisation des items
    items = []
    for it in b.get("items", []):
        ni = {
            "ref_type": it.get("ref_type"),
            "label": it.get("label"),
            "amount": it.get("amount"),
        }
        if "ref_id" in it:
            try:
                ni["ref_id"] = ObjectId(it["ref_id"]) if isinstance(it["ref_id"], str) else it["ref_id"]
            except InvalidId:
                return {"error": "items.ref_id doit être un ObjectId"}, 400
        items.append(_strip_none(ni))

    #  construction du document Mongo
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    doc = _strip_none({
        "patient_id": pid,
        "appointment_id": appt_id,
        "consultation_id": consult_id,
        "facility_id": fid,
        "invoice_no": b.get("invoice_no"),
        "amount": round(float(b["amount"]), 2),  # sécurité de précision
        "currency": b["currency"],
        "method": b.get("method", "cash"),
        "status": b.get("status", "pending"),
        "items": items if items else None,
        "due_date": due_date,
        "paid_at": paid_at,
        "created_at": now,
        "updated_at": now,
        "deleted": False,
    })

    #  insertion MongoDB
    try:
        ins = db.payments.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return {"error": "validation_mongo", "details": details}, 400

    #  retour
    return {"_id": str(ins.inserted_id)}, 201


# -----------------------------------------------------------
# GET /api/payments — liste (filtres par status, currency, etc.)
# -----------------------------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres ID
    try:
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    # Filtres simples
    if "status" in request.args:
        st = request.args["status"]
        if st not in _ALLOWED_STATUS:
            return {"error": f"status invalide ({'|'.join(_ALLOWED_STATUS)})"}, 400
        q["status"] = st
    if "currency" in request.args:
        q["currency"] = request.args["currency"]
    if "method" in request.args:
        q["method"] = request.args["method"]

    # Tri décroissant par date de création
    cur = current_app.db.payments.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200


# -----------------------------------------------------------
# GET /api/payments/<id> — détail d’un paiement
# -----------------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.payments.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)
