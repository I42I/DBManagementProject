# app.py
from flask import Flask, jsonify, request, g
from flask.json.provider import DefaultJSONProvider  # -> permet de personnaliser la sérialisation JSON
from flask_cors import CORS                         # -> CORS pour que le front (5173) appelle l'API (5000)
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, date, timezone
from logging.handlers import RotatingFileHandler
import logging, os, uuid

# =============================
# 1) App + JSON provider
# =============================
app = Flask(__name__)

class MongoJSON(DefaultJSONProvider):
    """Sérialise proprement les types Mongo/Datetime en JSON."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # ObjectId -> "64f..."
        if isinstance(o, (datetime, date)):
            # Forcer ISO 8601 en Z (UTC). Si datetime naïf, on le tag en UTC.
            if isinstance(o, datetime) and o.tzinfo is None:
                o = o.replace(tzinfo=timezone.utc)
            return o.isoformat().replace("+00:00", "Z")
        return super().default(o)

app.json = MongoJSON(app)

# CORS : autorise le front (Vite/5173). Ajoute d'autres origines si besoin.
CORS(app, resources={
    r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}
})

# =============================
# 2) Mode lecture seule (toggle par variable d'env)
# =============================
# Idée : en démo ou pendant la phase "GET only", on bloque POST/PATCH/DELETE.
READ_ONLY = os.getenv("READ_ONLY", "1").lower() in ("1", "true", "yes")

# @app.before_request
# def _enforce_read_only():
#     # On laisse passer les sondes de vie
#     if request.path in ("/health", "/api/health", "/ready"):
#         return
#     # Si READ_ONLY = True -> seules les requêtes GET/HEAD/OPTIONS passent
#     if READ_ONLY and request.method not in ("GET", "HEAD", "OPTIONS"):
#         return jsonify({"error": "read_only_mode", "message": "Writes are disabled"}), 405


# =============================
# 3) Logs avec rotation (évite d'avoir un fichier énorme)
# =============================
os.makedirs("logs", exist_ok=True)
handler = RotatingFileHandler("logs/backend_run.log", maxBytes=5_000_000, backupCount=5)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))

# IMPORTANT : ne pas empiler plusieurs handlers si le reloader relance l'app
if not app.logger.handlers:
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)

@app.before_request
def _request_id():
    # Un ID de requête pour tracer côté logs
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    app.logger.info(f"-> {g.request_id} {request.method} {request.path}")

@app.after_request
def _after(resp):
    # On renvoie l'ID dans la réponse (utile côté front/outils)
    resp.headers["X-Request-ID"] = g.get("request_id", "")
    app.logger.info(f"<- {g.request_id} {request.method} {request.path} {resp.status_code}")
    return resp

# =============================
# 4) Connexion MongoDB
# =============================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB", "hospital")

# Timeouts courts = fail fast si Mongo est down
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
app.db = client[DB_NAME]

# =============================
# 5) Index & Seed
# =============================
def ensure_minimal_indexes(db):
    """Ici, juste un TTL de démonstration (si jamais tu ajoutes expires_at sur notifications)."""
    try:
        db.notifications.create_index(
            "expires_at",
            name="ttl_expires_at",
            expireAfterSeconds=0
        )
        app.logger.info("[indexes] TTL notifications OK")
    except Exception as e:
        app.logger.warning(f"[indexes] TTL notifications skipped: {e}")

def bootstrap_indexes_and_seed():
    """Lancé une seule fois (voir garde reloader plus bas)."""
    ensure_minimal_indexes(app.db)
    try:
        if os.getenv("SEED_ON_START", "false").lower() in ("1", "true", "yes"):
            import seed  # seed.py à la racine backend
            if hasattr(seed, "load_seed"):
                seed.load_seed(app.db)
                app.logger.info("[seed] load_seed OK")
            elif hasattr(seed, "main"):
                try:
                    seed.main(app.db)  # préfère cette sig
                except TypeError:
                    seed.main()        # compat
                app.logger.info("[seed] main OK")
        else:
            app.logger.info("[seed] SEED_ON_START=false -> pas de seed.")
    except ModuleNotFoundError:
        app.logger.info("[seed] seed.py absent -> aucun seed.")
    except Exception as e:
        app.logger.exception(f"[seed] erreur de bootstrap: {e}")

# ⚠️ Garde pour éviter double bootstrap avec le reloader Flask
if not (os.getenv("FLASK_DEBUG", "0").lower() in ("1","true","yes")
        and os.getenv("WERKZEUG_RUN_MAIN") != "true"):
    bootstrap_indexes_and_seed()

# =============================
# 6) Health / Ready
# =============================
@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/api/health")
def api_health():
    return health()

@app.get("/ready")
def ready():
    try:
        client.admin.command("ping")
        return {"status": "ready"}, 200
    except Exception as e:
        app.logger.exception(e)
        return {"status": "not-ready", "error": str(e)}, 503

# =============================
# 7) Error handlers uniformes
# =============================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found", "details": str(e)}), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad Request", "details": str(e)}), 400

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method Not Allowed"}), 405

@app.errorhandler(422)
def unprocessable(e):
    return jsonify({"error": "Unprocessable Entity", "details": str(e)}), 422

@app.errorhandler(500)
def server_error(e):
    app.logger.exception(e)
    return jsonify({"error": "Internal Server Error"}), 500

# =============================
# 8) Blueprints (routes)
# =============================
from routes.patients import bp as patients_bp
from routes.doctors import bp as doctors_bp
from routes.appointments import bp as appointments_bp
from routes.prescriptions import bp as prescriptions_bp
from routes.consultations import bp as consultations_bp
from routes.laboratories import bp as laboratories_bp
from routes.pharmacies import bp as pharmacies_bp
from routes.payments import bp as payments_bp
from routes.notifications import bp as notifications_bp
from routes.health_authorities import bp as ha_bp
from routes.contacts import bp as contacts_bp

app.register_blueprint(patients_bp,        url_prefix="/api/patients")
app.register_blueprint(doctors_bp,         url_prefix="/api/doctors")
app.register_blueprint(appointments_bp,    url_prefix="/api/appointments")
app.register_blueprint(prescriptions_bp,   url_prefix="/api/prescriptions")
app.register_blueprint(consultations_bp,   url_prefix="/api/consultations")
app.register_blueprint(laboratories_bp,    url_prefix="/api/laboratories")
app.register_blueprint(pharmacies_bp,      url_prefix="/api/pharmacies")
app.register_blueprint(payments_bp,        url_prefix="/api/payments")
app.register_blueprint(notifications_bp,   url_prefix="/api/notifications")
app.register_blueprint(ha_bp,              url_prefix="/api/health_authorities")
app.register_blueprint(contacts_bp, url_prefix="/api/contacts")


# =============================
# 9) Main
# =============================
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    # use_reloader=debug : pratique en dev. En prod -> False.
    app.run(host="0.0.0.0", port=5000, debug=debug, use_reloader=debug)
