from flask import current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from functools import wraps

def strip_none(d: dict) -> dict:
    """Supprime les clés dont la valeur est None."""
    return {k: v for k, v in d.items() if v is not None}

def iso_to_dt(val, field_name: str | None = None):
    """
    Convertit une chaîne ISO (ou datetime) en datetime aware UTC.
    - val: str | datetime | None
    - field_name: nom du champ (optionnel) utilisé dans le message d'erreur

    Retourne datetime ou None si val est falsy.
    Lève ValueError si la conversion échoue.
    """
    if val is None or val == "":
        return None

    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)

    if not isinstance(val, str):
        raise ValueError(f"{field_name or 'date'} invalide")

    s = val.strip()
    # support 'Z' suffix
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        # assure timezone
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        raise ValueError(f"{field_name or 'date'} invalide")

def validate_objectid(id_str: str, field_name: str = "ID"):
    """Valide un ObjectId, lève une exception 400 si invalide."""
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise ValueError(f"{field_name} invalide")

def check_exists(coll: str, doc_id: ObjectId, field_name: str):
    """Vérifie l'existence d'un document, lève une exception 404 si absent."""
    if not current_app.db[coll].find_one({"_id": doc_id}, {"_id": 1}):
        raise FileNotFoundError(f"{field_name} introuvable")