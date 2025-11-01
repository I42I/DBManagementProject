# ===========================================================
#  prescriptions.py — Gestion des ordonnances
#  Auteur : Yaya Issakha (ECAM - projet NoSQL)
#  Rôle :
#    - Créer une prescription (liée patient / médecin / consultation)
#    - Lister les prescriptions (filtres par IDs + période)
#    - Détail d’une prescription
#  Points clés :
#    - Validation douce des types (items, notes, etc.)
#    - Suppression des champs None avant insertion
#    - Coercition de 'renouvellements' en entier >= 0
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("prescriptions", __name__)

# -------------------------------
# Helpers génériques
# -------------------------------
def _strip_none(d: dict) -> dict:
    """Supprime les clés dont la valeur est None (évite d'écrire null)."""
    return {k: v for k, v in d.items() if v is not None}

def _to_dt(s: str):
    """Chaîne ISO8601 -> datetime avec tz UTC (pour les filtres)."""
    if not isinstance(s, str):
        return None
    try:
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

# -------------------------------
# Validation d'entrée
# -------------------------------
def _validate_create(b: dict):
    # Champs obligatoires
    for f in ("patient_id", "doctor_id", "consultation_id", "items"):
        if f not in b:
            return f"{f} requis"

    # items : tableau non vide
    if not isinstance(b["items"], list) or len(b["items"]) == 0:
        return "items doit être un tableau non vide"

    # chaque item doit contenir dci + posologie (string non vide)
    for it in b["items"]:
        if not isinstance(it, dict):
            return "chaque item doit être un objet"
        if "dci" not in it or not isinstance(it["dci"], str) or not it["dci"].strip():
            return "chaque item doit contenir dci (string non vide)"
        if "posologie" not in it or not isinstance(it["posologie"], str) or not it["posologie"].strip():
            return "chaque item doit contenir posologie (string non vide)"

        # Validation douce des autres champs si présents
        if "forme" in it and it["forme"] is not None and not isinstance(it["forme"], str):
            return "items[].forme doit être une chaîne si présent"
        if "duree_j" in it and it["duree_j"] is not None:
            try:
                dj = int(it["duree_j"])
                if dj < 0: return "items[].duree_j doit être >= 0"
            except Exception:
                return "items[].duree_j doit être un entier"
        if "contre_indications" in it and it["contre_indications"] is not None and not isinstance(it["contre_indications"], str):
            return "items[].contre_indications doit être une chaîne si présent"

    # notes optionnel : string si présent
    if "notes" in b and b["notes"] is not None and not isinstance(b["notes"], str):
        return "notes doit être une chaîne si présent"

    # renouvellements optionnel : entier >= 0
    if "renouvellements" in b and b["renouvellements"] is not None:
        try:
            if int(b["renouvellements"]) < 0:
                return "renouvellements doit être >= 0"
        except Exception:
            return "renouvellements doit être un entier"

    return None

def _normalize_items(items_in):
    """
    Conserve uniquement les champs autorisés et enlève les None.
    Autorisés : dci, forme, posologie, duree_j, contre_indications
    """
    out = []
    for it in items_in:
        item = {
            "dci": it.get("dci").strip() if isinstance(it.get("dci"), str) else it.get("dci"),
            "forme": it.get("forme").strip() if isinstance(it.get("forme"), str) else it.get("forme"),
            "posologie": it.get("posologie").strip() if isinstance(it.get("posologie"), str) else it.get("posologie"),
            "duree_j": int(it["duree_j"]) if it.get("duree_j") is not None else None,
            "contre_indications": it.get("contre_indications").strip()
                if isinstance(it.get("contre_indications"), str) else it.get("contre_indications"),
        }
        out.append(_strip_none(item))
    return out

# -------------------------------
# POST /api/prescriptions — créer
# -------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # 1) Validation d'entrée
    err = _validate_create(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # 2) Cast ObjectId obligatoires
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
        cid = ObjectId(b["consultation_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id/consultation_id doivent être des ObjectId"}, 400

    # 3) Existence de base
    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404
    if not db.consultations.find_one({"_id": cid}):
        return {"error": "consultation introuvable"}, 404

    # 4) facility_id optionnel (non requis par ton schéma) -> cast si fourni
    fid = None
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400

    # 5) Normalisation des items
    items = _normalize_items(b["items"])

    # 6) Coercition renouvellements (défaut = 0)
    try:
        renouvel = int(b.get("renouvellements", 0))
        if renouvel < 0:
            renouvel = 0
    except Exception:
        renouvel = 0

    # 7) Construction du document
    doc = {
        "patient_id": pid,
        "doctor_id": did,
        "consultation_id": cid,
        "items": items,
        "renouvellements": renouvel,
        "notes": b.get("notes"),
        "created_at": datetime.utcnow().replace(tzinfo=timezone.utc),
        "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc),
        "deleted": False,
    }
    if fid:
        doc["facility_id"] = fid

    # 8) Suppression des None
    doc = _strip_none(doc)

    # 9) Insertion
    try:
        ins = db.prescriptions.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return {"error": "validation_mongo", "details": details}, 400

    return {"_id": str(ins.inserted_id)}, 201

# -----------------------------------------
# GET /api/prescriptions — liste (filtres)
# -----------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres par identifiants
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

    # Filtres de période (sur created_at)
    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")
    if date_from or date_to:
        rng = {}
        if date_from:
            df = _to_dt(date_from)
            if not df: return {"error": "date_from doit être ISO 8601"}, 400
            rng["$gte"] = df
        if date_to:
            dt_ = _to_dt(date_to)
            if not dt_: return {"error": "date_to doit être ISO 8601"}, 400
            rng["$lte"] = dt_
        q["created_at"] = rng

    cur = current_app.db.prescriptions.find(q).sort("created_at", -1).limit(200)
    return [d for d in cur], 200

# --------------------------------------------------
# GET /api/prescriptions/<id> — détail
# --------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.prescriptions.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)
