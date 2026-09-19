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

@application.route("/pending_orders", methods=["GET"])
@jwt_required()
def pending_orders():

    claims = get_jwt()

    if "director" not in claims.get("role", []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    orders = []

    order_uuids = redis_client.smembers("pending_orders")

    for order_uuid in order_uuids:

        order_data = redis_client.get(f"order:{order_uuid}")

        if order_data is not None:
            order = json.loads(order_data)
            orders.append(order)

    return jsonify({"orders": orders}), 200

@application.route("/decision", methods=["POST"])
@jwt_required()
def decision():

    claims = get_jwt()

    if "director" not in claims.get("role", []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    data = request.get_json(silent=True)

    if data is None:
        data = {}

    if "uuid" not in data or data["uuid"] == "":
        return jsonify({
            "message": "Field uuid is missing."
        }), 400

    uuid_value = data["uuid"]


    try:
        uuid.UUID(uuid_value)
    except (ValueError, AttributeError, TypeError):
        return jsonify({
            "message": "Invalid uuid."
        }), 400

    order_key = f"order:{uuid_value}"
    order_data = redis_client.get(order_key)

    if order_data is None or not redis_client.sismember(
        "pending_orders",
        uuid_value
    ):
        return jsonify({
            "message": "Invalid uuid."
        }), 400

    if "approved" not in data:
        return jsonify({
            "message": "Field approved is missing."
        }), 400

    if not isinstance(data["approved"], bool):
        return jsonify({
            "message": "Invalid decision."
        }), 400

    approved = data["approved"]

    if not approved:
        redis_client.srem("pending_orders", uuid_value)
        redis_client.delete(order_key)

        return "", 200

    order = json.loads(order_data)

    order_type = order.get("order_type")

    if order_type == "BUY":

        asset = {
            "name": order["name"],
            "categories": order["categories"],
            "buying_price": order["buying_price"],
            "buying_date": datetime.utcnow(),
            "info": order["info"]
        }

        assets_collection.insert_one(asset)

    elif order_type == "SELL":

        assets_collection.update_one(
            {
                "_id": __import__("bson").ObjectId(order["id"])
            },
            {
                "$set": {
                    "selling_price": order["selling_price"],
                    "selling_date": datetime.utcnow()
                }
            }
        )

    else:
        return jsonify({
            "message": "Invalid order type."
        }), 400

    redis_client.srem("pending_orders", uuid_value)
    redis_client.delete(order_key)

    return "", 200

@application.route("/report", methods=["GET"])
@jwt_required()
def report():

    claims = get_jwt()

    if "director" not in claims.get("role", []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    pipeline = [
        {
            "$unwind": "$categories"
        },
        {
            "$group": {
                "_id": "$categories",

                "spent": {
                    "$sum": "$buying_price"
                },

                "earned": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$selling_price", None]},
                                    {"$ne": ["$selling_date", None]}
                                ]
                            },
                            "$selling_price",
                            0
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "spent": 1,
                "earned": 1
            }
        },
        {
            "$sort": {
                "earned": -1,
                "spent": 1,
                "category": 1
            }
        }
    ]

    result = list(assets_collection.aggregate(pipeline))

    return jsonify({
        "statistics": result
    }), 200


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5002)