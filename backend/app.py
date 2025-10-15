from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB", "hospital")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def oid(x): return ObjectId(x) if isinstance(x, str) else x

@app.get("/health")
def health():
    return {"status":"ok"}, 200


# patient 

@app.get("/api/patients")
def list_patients():
    cur = db.patients.find({}, {"identite":1, "contacts.phone":1}).limit(50)
    res = [{**doc, "_id": str(doc["_id"])} for doc in cur]
    return jsonify(res), 200

@app.post("/api/patients")
def create_patient():
    data = request.json or {}
    # valeurs par défaut minimales
    data.setdefault("facility_id", ObjectId())
    data.setdefault("created_at", datetime.utcnow())
    data.setdefault("updated_at", datetime.utcnow())
    ins = db.patients.insert_one(data)
    return {"_id": str(ins.inserted_id)}, 201


#doctors

@app.get("/api/doctors")
def list_doctors():
    cur = db.medecins.find({}, {"identite":1, "specialites":1}).limit(50)
    res = [{**doc, "_id": str(doc["_id"])} for doc in cur]
    return jsonify(res), 200

@app.post("/api/doctors")
def create_doctor():
    data = request.json or {}
    data.setdefault("facility_id", ObjectId())
    data.setdefault("created_at", datetime.utcnow())
    data.setdefault("updated_at", datetime.utcnow())
    ins = db.medecins.insert_one(data)
    return {"_id": str(ins.inserted_id)}, 201
