from flask import Flask
from flask.json.provider import DefaultJSONProvider
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, date, timezone
import os

app = Flask(__name__)

class MongoJSON(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, date)):
            if isinstance(o, datetime) and o.tzinfo is None:
                o = o.replace(tzinfo=timezone.utc)
            return o.isoformat().replace('+00:00', 'Z')
        return super().default(o)

app.json = MongoJSON(app)

# Mongo
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB", "hospital")
client = MongoClient(MONGO_URI)
app.db = client[DB_NAME]

@app.get("/health")
def health():
    return {"status": "ok"}, 200

# alias for scripts/clients that expect /api/health
@app.get("/api/health")
def api_health():
    return health()

# Blueprints
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

if __name__ == "__main__":
    # enable debug/reloader only when FLASK_DEBUG=1/true is set
    _debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=5000, debug=_debug, use_reloader=_debug)


