# ===========================================================
#  health_authorities.py — Rapports vers l'autorité de santé
# 
#
#  Endpoints:
#    POST /api/health_authorities        -> créer un rapport
#    GET  /api/health_authorities        -> lister (filtres)
#    GET  /api/health_authorities/<id>   -> détail
#
#  Points clés :
#    - Validation stricte (report_type, period_start/end, status…)
#    - Conversion ISO8601 → datetime aware (UTC)
#    - Nettoyage des None pour respecter $jsonSchema
#    - Même style que le reste de l’API (appointments, consultations…)
# ===========================================================

from flask import Blueprint, request, current_app, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("health_authorities", __name__)  # url_prefix="/api/health_authorities" dans app.py

ALLOWED_REPORT_TYPES = {"case_summary", "disease_reporting", "inventory", "other"}
ALLOWED_STATUS = {"draft", "submitted", "accepted", "rejected"}

# -------------------------------
# Helpers
# -------------------------------
def _iso_to_dt(v, field_name: str):
    """Convertit ISO8601 (avec ou sans Z) en datetime aware (UTC)."""
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if not isinstance(v, str):
        raise ValueError(f"{field_name} doit être une date ISO 8601")
    try:
        s = v.replace("Z", "+00:00") if v.endswith("Z") else v
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        raise ValueError(f"{field_name} doit être une date ISO 8601")

def _strip_none(d: dict):
    """Supprime les clés dont la valeur est None (propre pour les validateurs Mongo)."""
    return {k: v for k, v in d.items() if v is not None}

def _jsonify(doc):
    """Cast ObjectId/datetime -> types JSON-safe + normalise datetime en UTC (suffixe Z)."""
    if not doc:
        return doc
    d = dict(doc)
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
        elif isinstance(v, datetime):
            v = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            d[k] = v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return d

def _validate(b: dict):
    """Contrôles fonctionnels d’entrée."""
    for f in ("report_type", "period_start", "period_end", "status", "facility_id"):
        if f not in b:
            return f"{f} requis"
    if b.get("report_type") not in ALLOWED_REPORT_TYPES:
        return f"report_type invalide ({'|'.join(sorted(ALLOWED_REPORT_TYPES))})"
    if b.get("status") not in ALLOWED_STATUS:
        return f"status invalide ({'|'.join(sorted(ALLOWED_STATUS))})"
    # payload optionnel mais s'il existe => dict
    if "payload" in b and b["payload"] is not None and not isinstance(b["payload"], dict):
        return "payload doit être un objet"
    return None

# -------------------------------
# POST /api/health_authorities — création
# -------------------------------
@bp.post("")
def create():
    b = request.get_json(silent=True) or {}

    # Validation fonctionnelle
    err = _validate(b)
    if err:
        return jsonify(error=err), 400

    # Cast IDs
    try:
        facility_id = ObjectId(b["facility_id"])
    except InvalidId:
        return jsonify(error="facility_id doit être un ObjectId"), 400
    # (Option : vérifier existence dans db.facilities si on a la collection)

    # Dates de période (obligatoires)
    try:
        period_start = _iso_to_dt(b["period_start"], "period_start")
        period_end   = _iso_to_dt(b["period_end"], "period_end")
    except ValueError as e:
        return jsonify(error=str(e)), 400

    if period_end < period_start:
        return jsonify(error="period_end doit être >= period_start"), 400

    # Statut + dates optionnelles
    submitted_at = None
    if b.get("submitted_at"):
        try:
            submitted_at = _iso_to_dt(b["submitted_at"], "submitted_at")
        except ValueError as e:
            return jsonify(error=str(e)), 400

    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    # Document propre pour Mongo
    doc = _strip_none({
        "facility_id": facility_id,
        "report_type": b["report_type"],
        "period_start": period_start,
        "period_end": period_end,
        "status": b.get("status", "draft"),
        "payload": b.get("payload") if isinstance(b.get("payload"), dict) else None,
        "external_ref": str(b["external_ref"]) if b.get("external_ref") is not None else None,
        "notes": str(b["notes"]) if b.get("notes") is not None else None,
        "submitted_at": submitted_at,
        "created_at": now,
        "updated_at": now,
        "deleted": False,
    })

    # Insertion + gestion erreur Mongo
    try:
        ins = current_app.db.health_authorities.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return jsonify(error="validation_mongo", details=details), 400

    return jsonify(_id=str(ins.inserted_id)), 201

# -------------------------------
# GET /api/health_authorities — liste
# -------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres simples (id + enums)
    if "facility_id" in request.args:
        try:
            q["facility_id"] = ObjectId(request.args["facility_id"])
        except InvalidId:
            return jsonify(error="facility_id invalide"), 400

    if "report_type" in request.args:
        rt = request.args["report_type"]
        if rt not in ALLOWED_REPORT_TYPES:
            return jsonify(error=f"report_type invalide ({'|'.join(sorted(ALLOWED_REPORT_TYPES))})"), 400
        q["report_type"] = rt

    if "status" in request.args:
        st = request.args["status"]
        if st not in ALLOWED_STATUS:
            return jsonify(error=f"status invalide ({'|'.join(sorted(ALLOWED_STATUS))})"), 400
        q["status"] = st

    # (Option) Filtres de période : ?from=YYYY…&to=YYYY… sur created_at
    # if "from" in request.args or "to" in request.args:
    #     rng = {}
    #     if "from" in request.args:
    #         rng["$gte"] = _iso_to_dt(request.args["from"], "from")
    #     if "to" in request.args:
    #         rng["$lte"] = _iso_to_dt(request.args["to"], "to")
    #     q["created_at"] = rng

    cur = current_app.db.health_authorities.find(q).sort("created_at", -1).limit(200)
    return jsonify([_jsonify(d) for d in cur]), 200

# -------------------------------
# GET /api/health_authorities/<id> — détail
# -------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return jsonify(error="id invalide"), 400
    d = current_app.db.health_authorities.find_one({"_id": oid})
    return (jsonify(_jsonify(d)), 200) if d else (jsonify(error="introuvable"), 404)
