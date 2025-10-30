from flask import Flask, jsonify, request, g
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, date, timezone
from logging.handlers import RotatingFileHandler
import logging, os, uuid

# -----------------------------
# App & JSON provider
# -----------------------------
app = Flask(__name__)

class MongoJSON(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, date)):
            # force ISO8601 en Z (UTC)
            if isinstance(o, datetime) and o.tzinfo is None:
                o = o.replace(tzinfo=timezone.utc)
            return o.isoformat().replace("+00:00", "Z")
        return super().default(o)

app.json = MongoJSON(app)

# CORS (par défaut permissif ; ajuste si besoin avec origins=[...])
CORS(app)  # CORS(app, resources={r"/api/*": {"origins": "*"}})

READ_ONLY = os.getenv("READ_ONLY", "1").lower() in ("1", "true", "yes")

@app.before_request
def _enforce_read_only():
    # laissons passer health/ready
    if request.path in ("/health", "/api/health", "/ready"):
        return
    if READ_ONLY and request.method not in ("GET", "HEAD", "OPTIONS"):
        return jsonify({"error": "read_only_mode", "message": "Writes are disabled"}), 405

# -----------------------------
# Logs avec rotation
# -----------------------------
os.makedirs("logs", exist_ok=True)
handler = RotatingFileHandler("logs/backend_run.log", maxBytes=5_000_000, backupCount=5)
handler.setLevel(logging.INFO)
fmt = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
handler.setFormatter(fmt)

# Evite d'empiler des handlers si le reloader Flask relance le process
if not app.logger.handlers:
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)

@app.before_request
def _request_id():
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    app.logger.info(f"-> {g.request_id} {request.method} {request.path}")

@app.after_request
def _after(resp):
    resp.headers["X-Request-ID"] = g.get("request_id", "")
    app.logger.info(f"<- {g.request_id} {request.method} {request.path} {resp.status_code}")
    return resp

# -----------------------------
# Mongo
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB", "hospital")

# petits timeouts pour fail fast si Mongo est down
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
app.db = client[DB_NAME]

# -----------------------------
# Index & Seed (léger)
# -----------------------------
def ensure_minimal_indexes(db):
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
    ensure_minimal_indexes(app.db)
    try:
        if os.getenv("SEED_ON_START", "false").lower() in ("1", "true", "yes"):
            import seed  # seed.py
            if hasattr(seed, "load_seed"):
                seed.load_seed(app.db)
                app.logger.info("[seed] load_seed OK")
            elif hasattr(seed, "main"):
                try:
                    seed.main(app.db)
                except TypeError:
                    seed.main()
                app.logger.info("[seed] main OK")
        else:
            app.logger.info("[seed] SEED_ON_START=false -> pas de seed.")
    except ModuleNotFoundError:
        app.logger.info("[seed] seed.py absent -> aucun seed.")
    except Exception as e:
        app.logger.exception(f"[seed] erreur de bootstrap: {e}")

# Appelé à l’import (dès le démarrage du process)
bootstrap_indexes_and_seed()

# -----------------------------
# Health / Ready
# -----------------------------
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

# -----------------------------
# Error handlers uniformes
# -----------------------------
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

# -----------------------------
# Blueprints
# -----------------------------
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

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    _debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    # use_reloader=_debug : pratique en dev. En prod, laisse False.
    app.run(host="0.0.0.0", port=5000, debug=_debug, use_reloader=_debug)
