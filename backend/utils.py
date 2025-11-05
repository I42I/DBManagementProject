from flask import current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from functools import wraps

def strip_none(d: dict) -> dict:
    """Supprime les clés dont la valeur est None."""
    return {k: v for k, v in d.items() if v is not None}

def iso_to_dt(s: str | datetime | None) -> datetime | None:
    """Convertit une date ISO 8601 en datetime UTC."""
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    if not isinstance(s, str):
        return None
    try:
        s = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None

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