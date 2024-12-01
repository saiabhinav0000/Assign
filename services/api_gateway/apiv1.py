from flask import Flask, request, jsonify
from flask.json import JSONEncoder as BaseJSONEncoder
import os
from pymongo import MongoClient
import certifi
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Custom JSONEncoder for MongoDB ObjectId
class JSONEncoder(BaseJSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return BaseJSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

# MongoDB Configuration with SSL
MONGODB_URI = os.getenv('MONGODB_URI', "mongodb+srv://mongo:ipW272wjb1fwWRSi@cluster0.efff1.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where()
)
db = client.userDB
order_db = client.orderDB

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the API Gateway",
        "status": "running"
    })

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        if not all(key in data for key in ['userId', 'email', 'deliveryAddress']):
            return jsonify({"error": "Missing required fields"}), 400

        if db.users.find_one({"userId": data['userId']}):
            return jsonify({"error": "User already exists"}), 409

        new_user = {
            "userId": data['userId'],
            "email": data['email'],
            "deliveryAddress": data['deliveryAddress']
        }
        
        result = db.users.insert_one(new_user)
        new_user['_id'] = str(result.inserted_id)
        return jsonify({
            "message": "User created successfully",
            "user": new_user
        }), 201

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        required_fields = ['orderId', 'userId', 'userEmail', 'deliveryAddress', 'items']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Check if user exists
        user = db.users.find_one({"userId": data['userId']})
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check if order exists
        if order_db.orders.find_one({"orderId": data['orderId']}):
            return jsonify({"error": "Order already exists"}), 409

        new_order = {
            "orderId": data['orderId'],
            "userId": data['userId'],
            "userEmail": data['userEmail'],
            "deliveryAddress": data['deliveryAddress'],
            "items": data['items'],
            "orderStatus": "under process"
        }

        result = order_db.orders.insert_one(new_order)
        new_order['_id'] = str(result.inserted_id)
        return jsonify({
            "message": "Order created successfully",
            "order": new_order
        }), 201

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({"error": str(e)}), 400
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.json
        
        # Verify user exists
        existing_user = db.users.find_one({"userId": user_id})
        if not existing_user:
            return jsonify({"error": "User not found"}), 404

        # Prepare update data
        update_data = {}
        if 'email' in data:
            update_data['email'] = data['email']
        if 'deliveryAddress' in data:
            update_data['deliveryAddress'] = data['deliveryAddress']

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Update user
        result = db.users.update_one(
            {"userId": user_id},
            {"$set": update_data}
        )

        if result.modified_count:
            # Update corresponding orders
            order_update = {}
            if 'email' in update_data:
                order_update['userEmail'] = update_data['email']
            if 'deliveryAddress' in update_data:
                order_update['deliveryAddress'] = update_data['deliveryAddress']

            if order_update:
                order_db.orders.update_many(
                    {"userId": user_id},
                    {"$set": order_update}
                )

            return jsonify({
                "message": "User and related orders updated successfully",
                "updates": update_data
            }), 200

        return jsonify({
            "message": "No changes made",
            "current_values": {
                "email": existing_user['email'],
                "deliveryAddress": existing_user['deliveryAddress']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        data = request.json
        new_status = data.get('orderStatus')
        
        if new_status not in ['under process', 'shipping', 'delivered']:
            return jsonify({"error": "Invalid order status"}), 400

        result = order_db.orders.update_one(
            {"orderId": order_id},
            {"$set": {"orderStatus": new_status}}
        )

        if result.modified_count:
            updated_order = order_db.orders.find_one({"orderId": order_id})
            return jsonify({
                "message": "Order status updated successfully",
                "order": updated_order
            }), 200
        
        return jsonify({"error": "Order not found"}), 404

    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        user_id = request.args.get('userId')
        if not user_id:
            return jsonify({"error": "userId parameter is required"}), 400

        orders = list(order_db.orders.find({"userId": user_id}))
        return jsonify({
            "message": "Orders retrieved successfully",
            "orders": orders
        }), 200

    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)