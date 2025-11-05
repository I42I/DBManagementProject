# app.py
from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS                         # -> CORS pour que le front (5173) appelle l'API (5000)
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, date, timezone
from logging.handlers import RotatingFileHandler
import logging, os, uuid
from pathlib import Path

# =============================
# 1) App + JSON provider
# =============================
app = Flask(__name__)

class MongoJSON(app.json_provider_class):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, date)):
            if isinstance(o, datetime) and o.tzinfo is None:
                o = o.replace(tzinfo=timezone.utc)
            return o.isoformat().replace("+00:00", "Z")
        return super().default(o)

app.json = MongoJSON(app)

STATIC_DIR = Path(__file__).resolve().parent / "static"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    target = STATIC_DIR / path
    if path and target.exists():
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")

CORS(app, resources={r"/api/*": {"origins": "*"}})


# =============================
# 2) Logs avec rotation (évite d'avoir un fichier énorme)
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
# 3) Connexion MongoDB
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
# 4) Index & Seed
# =============================
def bootstrap():
    if os.getenv("SEED_ON_START", "false").lower() in ("1", "true", "yes"):
        try:
            import seed
            seed.load_seed(app.db) if hasattr(seed, "load_seed") else seed.main(app.db)
            app.logger.info("[seed] done")
        except Exception as exc:
            app.logger.warning("[seed] skipped: %s", exc)

bootstrap()

# =============================
# 5) Health / Ready
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
# 6) Error handlers uniformes
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
# 7) Blueprints (routes)
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
app.register_blueprint(contacts_bp,        url_prefix="/api/contacts")


# =============================
# 8) Main
# =============================
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    # use_reloader=debug : pratique en dev. En prod -> False.
    app.run(host="0.0.0.0", port=5000, debug=debug, use_reloader=debug)
