# ===========================================================
#  laboratories.py — Gestion des analyses de laboratoire
#  
#  Rôle :
#    - Créer un document de laboratoire (ordonnance d’analyses)
#    - Lister les analyses filtrables par patient, médecin, statut, etc.
#    - Consulter le détail d’une analyse
#  Points clés :
#    - Validation stricte des champs (tests[], status…)
#    - Suppression des champs None pour respecter le validator Mongo
#    - Génération automatique de facility_id et gestion du status
# ===========================================================

from flask import Blueprint, request, current_app
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from datetime import datetime, timezone

bp = Blueprint("laboratories", __name__)

# -----------------------------------------------------------
# Statuts autorisés pour le champ "status"
# -----------------------------------------------------------
_ALLOWED_STATUS = {"ordered", "in_progress", "completed", "cancelled"}


# -----------------------------------------------------------
# Utils : suppression des clés None (évite null dans Mongo)
# -----------------------------------------------------------
def _strip_none(d: dict):
    """Supprime les clés dont la valeur est None (évite d’écrire null)."""
    return {k: v for k, v in d.items() if v is not None}


# -----------------------------------------------------------
# Validation du corps JSON lors d’une création
# -----------------------------------------------------------
def _validate(b):
    # Champs obligatoires
    for f in ("patient_id", "doctor_id", "status"):
        if f not in b:
            return f"{f} requis"

    # Statut autorisé
    if b["status"] not in _ALLOWED_STATUS:
        return "status invalide (ordered|in_progress|completed|cancelled)"

    # Validation douce : notes string si présent
    if "notes" in b and b["notes"] is not None and not isinstance(b["notes"], str):
        return "notes doit être une chaîne si présent"

    # Tests (optionnels, mais typés si présents)
    if "tests" in b:
        if not isinstance(b["tests"], list):
            return "tests doit être un tableau"
        for t in b["tests"]:
            if not isinstance(t, dict):
                return "chaque test doit être un objet"

            # Champs obligatoires de chaque test
            for k in ("code", "name", "status"):
                if k not in t:
                    return f"tests[].{k} requis"
                if not isinstance(t[k], str) or not t[k].strip():
                    return f"tests[].{k} doit être une chaîne non vide"

            # Validation douce des champs optionnels
            if "result" in t and t["result"] is not None and not isinstance(t["result"], (int, float, str)):
                return "tests[].result doit être numérique ou texte"
            if "unit" in t and t["unit"] is not None and not isinstance(t["unit"], str):
                return "tests[].unit doit être une chaîne si présent"
            if "ref_range" in t and t["ref_range"] is not None and not isinstance(t["ref_range"], str):
                return "tests[].ref_range doit être une chaîne si présent"
            if "abnormal" in t and t["abnormal"] is not None and not isinstance(t["abnormal"], bool):
                return "tests[].abnormal doit être booléen si présent"

    return None


# -----------------------------------------------------------
# POST /api/laboratories — création d’une analyse
# -----------------------------------------------------------
@bp.post("")
def create():
    b = request.get_json(force=True) or {}

    # validation complète
    err = _validate(b)
    if err:
        return {"error": err}, 400

    db = current_app.db

    # conversion ObjectId et existence patient/médecin
    try:
        pid = ObjectId(b["patient_id"])
        did = ObjectId(b["doctor_id"])
    except InvalidId:
        return {"error": "patient_id/doctor_id doivent être des ObjectId"}, 400

    if not db.patients.find_one({"_id": pid}):
        return {"error": "patient introuvable"}, 404
    if not db.doctors.find_one({"_id": did}):
        return {"error": "médecin introuvable"}, 404

    # facility_id (généré si absent)
    if b.get("facility_id"):
        try:
            fid = ObjectId(b["facility_id"])
        except InvalidId:
            return {"error": "facility_id doit être un ObjectId"}, 400
    else:
        fid = ObjectId()  # généré automatiquement

    #  appointment_id optionnel
    ap_id = None
    if b.get("appointment_id"):
        try:
            ap_id = ObjectId(b["appointment_id"])
        except InvalidId:
            return {"error": "appointment_id doit être un ObjectId"}, 400
        if not db.appointments.find_one({"_id": ap_id}):
            return {"error": "appointment introuvable"}, 404

    # Normalisation des tests
    tests = []
    for t in b.get("tests", []):
        nt = {
            "code": t.get("code").strip() if isinstance(t.get("code"), str) else t.get("code"),
            "name": t.get("name").strip() if isinstance(t.get("name"), str) else t.get("name"),
            "status": t.get("status").strip() if isinstance(t.get("status"), str) else t.get("status"),
        }
        for k in ("result", "unit", "ref_range", "abnormal"):
            if t.get(k) is not None:
                nt[k] = t[k]
        tests.append(_strip_none(nt))

    # dates automatiques
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    date_reported = now if b.get("status") == "completed" else None

    # constitution du document Mongo
    doc = _strip_none({
        "patient_id": pid,
        "doctor_id": did,
        "facility_id": fid,
        "appointment_id": ap_id,
        "status": b.get("status", "ordered"),
        "date_ordered": now,
        "date_reported": date_reported,
        "tests": tests if tests else None,
        "notes": b.get("notes"),
        "created_at": now,
        "updated_at": now,
        "deleted": False,
    })

    # insertion en base
    try:
        ins = db.lab_results.insert_one(doc)
    except WriteError as we:
        details = getattr(we, "details", {}) or {}
        return {"error": "validation_mongo", "details": details}, 400

    return {"_id": str(ins.inserted_id)}, 201


# -----------------------------------------------------------
# GET /api/laboratories — liste filtrable
# -----------------------------------------------------------
@bp.get("")
def list_():
    q = {"deleted": {"$ne": True}}

    # Filtres simples par ID
    try:
        if "patient_id" in request.args:
            q["patient_id"] = ObjectId(request.args["patient_id"])
        if "doctor_id" in request.args:
            q["doctor_id"] = ObjectId(request.args["doctor_id"])
        if "facility_id" in request.args:
            q["facility_id"] = ObjectId(request.args["facility_id"])
    except InvalidId:
        return {"error": "paramètre id invalide"}, 400

    # Filtre par status
    if "status" in request.args:
        st = request.args["status"]
        if st not in _ALLOWED_STATUS:
            return {"error": f"status invalide ({'|'.join(_ALLOWED_STATUS)})"}, 400
        q["status"] = st

    # Filtre période optionnelle (date_from/date_to sur date_ordered)
    def _to_dt(s):
        try:
            s = s.replace("Z", "+00:00") if s.endswith("Z") else s
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")
    if date_from or date_to:
        rng = {}
        if date_from:
            df = _to_dt(date_from)
            if not df:
                return {"error": "date_from doit être ISO 8601"}, 400
            rng["$gte"] = df
        if date_to:
            dt_ = _to_dt(date_to)
            if not dt_:
                return {"error": "date_to doit être ISO 8601"}, 400
            rng["$lte"] = dt_
        q["date_ordered"] = rng

    cur = current_app.db.lab_results.find(q).sort("date_ordered", -1).limit(200)
    return [d for d in cur], 200


# -----------------------------------------------------------
# GET /api/laboratories/<id> — détail d'une analyse
# -----------------------------------------------------------
@bp.get("/<id>")
def get_one(id):
    try:
        oid = ObjectId(id)
    except InvalidId:
        return {"error": "id invalide"}, 400
    d = current_app.db.lab_results.find_one({"_id": oid})
    return (d, 200) if d else ({"error": "introuvable"}, 404)

