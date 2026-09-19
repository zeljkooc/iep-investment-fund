import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from datetime import datetime
import redis
import uuid
import json
from bson import ObjectId

application = Flask(__name__)
application.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

client = MongoClient(os.getenv("MONGO_URL"))
db = client[os.getenv("MONGO_DB")]

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

assets_collection = db["assets"]

jwt = JWTManager(application)

@application.route("/search", methods=["POST"])
@jwt_required()
def search():

    claims = get_jwt()

    if "employee" not in claims.get("role", []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    data = request.get_json() or {}
    query = {}

    if data.get("name"):
        query["name"] = {"$regex": data["name"], "$options": "i"}

    if data.get("category"):
        query["categories"] = data["category"]

    if data.get("buying_date"):
        query["buying_date"] = {
            "$gt": datetime.fromisoformat(
                data["buying_date"].replace("Z", "+00:00")
            )
        }

    if data.get("selling_date"):
        query["selling_date"] = {
            "$lt": datetime.fromisoformat(
                data["selling_date"].replace("Z", "+00:00")
            )
        }

    for f in data.get("info_filters", []):
        query["info." + f["field"]] = {
            "$" + f["operator"]: f["value"]
        }

    def _iso(dt):
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"

    result = []
    for x in db.assets.find(query):
        x["id"] = str(x["_id"])
        del x["_id"]
        if "buying_date" in x:
            x["buying_date"] = _iso(x["buying_date"])
        if "selling_date" in x:
            x["selling_date"] = _iso(x["selling_date"])
        result.append(x)

    return jsonify({"assets": result})

@application.route("/create_buy_order", methods=["POST"])
@jwt_required()
def create_buy_order():

    claims = get_jwt()

    if "employee" not in claims.get("role", []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    data = request.get_json()

    if data is None:
        data = {}

    if "name" not in data or data["name"] == "":
        return jsonify({
            "message": "Field name is missing."
        }), 400

    if "categories" not in data:
        return jsonify({
            "message": "Field categories is missing."
        }), 400

    if not isinstance(data["categories"], list):
        return jsonify({
            "message": "Categories list is empty."
        }), 400

    if len(data["categories"]) == 0:
        return jsonify({
            "message": "Categories list is empty."
        }), 400

    if "buying_price" not in data:
        return jsonify({
            "message": "Field buying_price is missing."
        }), 400

    if (
        not isinstance(data["buying_price"], (int, float))
        or isinstance(data["buying_price"], bool)
        or data["buying_price"] <= 0
    ):
        return jsonify({
            "message": "Invalid buying price."
        }), 400

    if "info" not in data:
        return jsonify({
            "message": "Field info is missing."
        }), 400

    if not isinstance(data["info"], dict):
        return jsonify({
            "message": "Field info is invalid."
        }), 400

    order_uuid = str(uuid.uuid4())

    order = {
        "uuid": order_uuid,
        "order_type": "BUY",
        "name": data["name"],
        "categories": data["categories"],
        "info": data["info"],
        "buying_price": data["buying_price"]
    }

    redis_client.set(
        f"order:{order_uuid}",
        json.dumps(order)
    )

    redis_client.sadd(
        "pending_orders",
        order_uuid
    )

    return "", 200

@application.route("/create_sell_order", methods=["POST"])
@jwt_required()
def create_sell_order():

    claims = get_jwt()

    if "employee" not in claims.get("role", []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    data = request.get_json(silent=True)

    if data is None:
        data = {}

    if "id" not in data or data["id"] == "":
        return jsonify({
            "message": "Field id is missing."
        }), 400

    try:
        asset_id = ObjectId(data["id"])
    except Exception:
        return jsonify({
            "message": "Invalid id."
        }), 400

    asset = assets_collection.find_one({
        "_id": asset_id
    })

    if asset is None:
        return jsonify({
            "message": "Invalid id."
        }), 400

    if "selling_price" not in data:
        return jsonify({
            "message": "Field selling_price is missing."
        }), 400

    selling_price = data["selling_price"]

    if (
        not isinstance(selling_price, (int, float))
        or isinstance(selling_price, bool)
        or selling_price <= 0
    ):
        return jsonify({
            "message": "Invalid selling price."
        }), 400

    order_uuid = str(uuid.uuid4())

    order = {
        "uuid": order_uuid,
        "order_type": "SELL",
        "id": str(asset_id),
        "selling_price": selling_price
    }

    redis_client.set(
        f"order:{order_uuid}",
        json.dumps(order)
    )

    redis_client.sadd(
        "pending_orders",
        order_uuid
    )

    return "", 200

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5001)