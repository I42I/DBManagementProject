import os, json, glob
from pymongo import MongoClient

DB_NAME  = os.getenv("MONGO_DB",  "hospital")
MONGO_URI= os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def jload(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_schema(coll, schema):
    if coll not in db.list_collection_names():
        db.create_collection(coll, validator={"$jsonSchema": schema})
        print(f"✔ created {coll}")
    else:
        db.command("collMod", coll, validator={"$jsonSchema": schema})
        print(f"✔ updated validator {coll}")

def ensure_indexes(coll, idx_list):
    for idx in idx_list:
        key = list(idx["key"].items())
        name = idx.get("name")
        unique = idx.get("unique", False)
        sparse = idx.get("sparse", False)
        db[coll].create_index(key, name=name, unique=unique, sparse=sparse)
    print(f"✔ indexes {coll}")

def main():
    base = os.path.dirname(__file__)
    for schema_path in glob.glob(os.path.join(base, "schemas", "*.json")):
        coll = os.path.splitext(os.path.basename(schema_path))[0]
        ensure_schema(coll, jload(schema_path))
        idx_path = os.path.join(base, "indexes", f"{coll}.indexes.json")
        if os.path.exists(idx_path):
            ensure_indexes(coll, jload(idx_path))
    print("✅ DB ready.")

if __name__ == "__main__":
    main()

