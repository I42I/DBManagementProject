# ===========================================================
#  notifications.py — Gestion des notifications (SMS / email / push)
#  Auteur : Yaya Issakha — ECAM (Projet NoSQL)
#
#  Endpoints:
#    POST   /api/notifications        -> créer une notification
#    GET    /api/notifications        -> lister (filtres)
#    GET    /api/notifications/<id>   -> détail
#
#  Points clés :
#    - Validation stricte des champs (channel, status, payload…)
#    - Conversion ISO8601 -> datetime UTC (send_at/sent_at/expires_at)
#    - Nettoyage des None pour éviter les erreurs de $jsonSchema
#    - Cohérence ref_type/ref_id (optionnelle mais contrôlée)
#    - Timestamps en UTC (compatibles avec l’index TTL sur expires_at)
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("notifications", __name__)

# Valeurs autorisées (garde cohérence avec ton $jsonSchema)
_ALLOWED_CHANNEL = {"sms", "email", "push"}
_ALLOWED_STATUS  = {"queued", "sent", "failed", "read"}
_ALLOWED_REF     = {"appointment", "consultation", "prescription", "payment", "other"}

# -------------------------------
# Helpers conversion / cast / clean
# -------------------------------
def _iso_to_dt(v):
    """Convertit une chaîne ISO8601 en datetime UTC (timezone-aware)."""
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
    """Tente de caster en ObjectId. Retourne None si invalide."""
    if v is None or isinstance(v, ObjectId):
        return v
    try:
        return ObjectId(v)
    except InvalidId:
        return None

def _strip_none(d: dict):
    """Supprime les clés dont la valeur est None (propre pour Mongo + validators)."""
    return {k: v for k, v in d.items() if v is not None}

# -------------------------------
# Validation d’entrée
# -------------------------------
def _validate(b: dict):
    for f in ("channel", "status"):
        if f not in b:
            return f"{f} requis"

    if b["channel"] not in _ALLOWED_CHANNEL:
        return "channel invalide (sms|email|push)"
    if b["status"] not in _ALLOWED_STATUS:
        return "status invalide (queued|sent|failed|read)"

    if "ref_type" in b and b["ref_type"] not in _ALLOWED_REF:
        return "ref_type invalide (appointment|consultation|prescription|payment|other)"

    # payload optionnel mais si présent -> objet
    if "payload" in b and b["payload"] is not None and not isinstance(b["payload"], dict):
        return "payload doit être un objet"

    # Cohérence optionnelle : si ref_id fourni, ref_type conseillé
    if b.get("ref_id") is not None and b.get("ref_type") is None:
        return "ref_type requis lorsque ref_id est fourni"

    return None

# -------------------------------
# POST /api/notifications — création
# -------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # 1) Validation fonctionnelle
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # 2) Cast des ObjectId optionnels
    to_pid = _cast_oid(b.get("to_patient_id"))
    if b.get("to_patient_id") is not None and to_pid is None:
        return {"error": "to_patient_id doit être un ObjectId"}, 400

    to_did = _cast_oid(b.get("to_doctor_id"))
    if b.get("to_doctor_id") is not None and to_did is None:
        return {"error": "to_doctor_id doit être un ObjectId"}, 400

    ref_id = _cast_oid(b.get("ref_id"))
    if b.get("ref_id") is not None and ref_id is None:
        return {"error": "ref_id doit être un ObjectId"}, 400

    # 3) Vérifications d’existence (optionnelles mais utiles)
    if to_pid and not db.patients.find_one({"_id": to_pid}, {"_id": 1}):
        return {"error": "to_patient_id introuvable"}, 404
    if to_did and not db.doctors.find_one({"_id": to_did}, {"_id": 1}):
        return {"error": "to_doctor_id introuvable"}, 404
    if ref_id and b.get("ref_type"):
        _ref_map = {
            "appointment": "appointments",
            "consultation": "consultations",
            "prescription": "prescriptions",
            "payment": "payments",
            "other": None,  # pas de vérif
        }
        coll = _ref_map.get(b["ref_type"])
        if coll and not db[coll].find_one({"_id": ref_id}, {"_id": 1}):
            return {"error": f"ref_id introuvable pour ref_type={b['ref_type']}"}, 404

    # 4) Dates optionnelles
    send_at    = _iso_to_dt(b.get("send_at"))    if b.get("send_at")    else None
    sent_at    = _iso_to_dt(b.get("sent_at"))    if b.get("sent_at")    else None
    expires_at = _iso_to_dt(b.get("expires_at")) if b.get("expires_at") else None

    if b.get("send_at") and not send_at:
        return {"error": "send_at doit être ISO 8601"}, 400
    if b.get("sent_at") and not sent_at:
        return {"error": "sent_at doit être ISO 8601"}, 400
    if b.get("expires_at") and not expires_at:
        return {"error": "expires_at doit être ISO 8601"}, 400

    # Si status=sent sans sent_at -> on positionne à maintenant (UTC)
    if b.get("status") == "sent" and not sent_at:
        sent_at = datetime.utcnow().replace(tzinfo=timezone.utc)

    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    # 5) Construction du document Mongo (pense à l’index TTL sur expires_at)
    doc = _strip_none({
        "channel": b["channel"],              # sms|email|push
        "status":  b["status"],               # queued|sent|failed|read
        "template": b.get("template"),        # ex: "appt_reminder"
        "payload":  b.get("payload") if isinstance(b.get("payload"), dict) else None,
        "ref_type": b.get("ref_type"),        # cf. _ALLOWED_REF
        "ref_id":   ref_id,
        "to_patient_id": to_pid,
        "to_doctor_id":  to_did,
        "send_at":    send_at,
        "sent_at":    sent_at,
        "expires_at": expires_at,             # TTL (défini dans ensure_indexes)
        "error": b.get("error"),
        "created_at": now,
        "updated_at": now,
        "deleted": False,
    })

    # 6) Insertion
    try:
        ins = db.notifications.insert_one(doc)
    except WriteError as we:
        return {"error": "validation_mongo", "details": getattr(we, "details", {}) or {}}, 400

    return {"_id": str(ins.inserted_id)}, 201

# -------------------------------
# GET /api/notifications — liste
# -------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres simples
    if "status" in request.args:
        q["status"] = request.args["status"]
    if "channel" in request.args:
        q["channel"] = request.args["channel"]
    if "ref_type" in request.args:
        q["ref_type"] = request.args["ref_type"]

    # Filtres par destinataires
    for arg in ("to_patient_id", "to_doctor_id"):
        if arg in request.args:
            oid = _cast_oid(request.args[arg])
            if oid is None:
                return {"error": f"{arg} invalide"}, 400
            q[arg] = oid

    cur = current_app.db.notifications.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

# -------------------------------
# GET /api/notifications/<id> — détail
# -------------------------------
@bp.get("/<id>")
def get_one(id):
    oid = _cast_oid(id)
    if oid is None:
        return {"error": "id invalide"}, 400
    d = current_app.db.notifications.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)
