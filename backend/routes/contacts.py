# ===========================================================
#  contacts.py — Réception des messages du formulaire de contact
#  Auteur : Yaya Issakha — ECAM (Projet NoSQL / Frontend intégration)
#
#  Endpoints:
#    POST /api/contacts  → enregistre un message envoyé depuis le site
#
#  Particularités :
#    - Pas de base de données (simple log console ou fichier)
#    - Vérifie la présence de name, email, message
#    - Affiche le message dans les logs serveur (utile pour débogage frontend)
# ===========================================================

from flask import Blueprint, request
from datetime import datetime

# On crée un "blueprint" pour ce module.
# Il sera monté dans app.py avec : app.register_blueprint(contacts.bp, url_prefix="/api/contacts")
bp = Blueprint("contacts", __name__)

# -------------------------------
# POST /api/contacts — réception d’un message
# -------------------------------
@bp.post("")
def create():
    """
    Reçoit un JSON depuis le frontend contenant :
      {
        "name": "John Doe",
        "email": "john@example.com",
        "message": "Bonjour, je voudrais en savoir plus sur votre service."
      }

    Vérifie que tous les champs sont présents et non vides.
    Log le contenu avec la date UTC, puis renvoie {"ok": True}.
    """
    b = request.get_json(force=True) or {}

    # Validation basique des 3 champs requis
    for f in ("name", "email", "message"):
        if not b.get(f):
            return {"error": f"{f} requis"}, 400

    # Log du message en console (remplaçable plus tard par envoi email / DB)
    print("[CONTACT]", datetime.utcnow().isoformat(), b)

    # Réponse standard
    return {"ok": True}, 200

