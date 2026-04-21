from flask import Blueprint, request, jsonify
from firebase_config import db
from firebase_admin import firestore
import uuid

product_bp = Blueprint('product', __name__)

# ─────────────────────────────────────────
# ADD PRODUCT (Admin)
# ─────────────────────────────────────────
@product_bp.route('/add', methods=['POST'])
def add_product():
    data = request.json
    product_id = str(uuid.uuid4())

    product = {
        "product_id": product_id,
        "name": data.get('name'),
        "brand": data.get('brand'),
        "appliance_type": data.get('appliance_type'),
        "condition": data.get('condition', 'new'),   # new / refurbished
        "price": data.get('price'),
        "energy_rating": data.get('energy_rating'),  # 1-5 stars
        "description": data.get('description'),
        "image_url": data.get('image_url', ''),
        "in_stock": True,
        "created_at": firestore.SERVER_TIMESTAMP
    }

    db.collection('products').document(product_id).set(product)
    return jsonify({"message": "Product added", "product_id": product_id}), 201


# ─────────────────────────────────────────
# GET ALL PRODUCTS (with optional filters)
# ─────────────────────────────────────────
@product_bp.route('/all', methods=['GET'])
def get_products():
    try:
        appliance_type = request.args.get('appliance_type')
        condition = request.args.get('condition')
        max_price = request.args.get('max_price')

        query = db.collection('products').where('in_stock', '==', True)

        if appliance_type:
            query = query.where('appliance_type', '==', appliance_type)
        if condition:
            query = query.where('condition', '==', condition)

        products = query.stream()
        result = [p.to_dict() for p in products]

        if max_price:
            result = [p for p in result if p.get('price', 0) <= float(max_price)]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# SUBMIT OLD APPLIANCE EXCHANGE
# ─────────────────────────────────────────
@product_bp.route('/exchange', methods=['POST'])
def submit_exchange():
    data = request.json
    exchange_id = str(uuid.uuid4())

    # Simple estimated exchange value logic
    age = data.get('age_years', 5)
    base_value = data.get('original_price', 5000)
    depreciation = 0.15 * age
    exchange_value = round(base_value * max(0.1, (1 - depreciation)))

    exchange = {
        "exchange_id": exchange_id,
        "customer_uid": data.get('customer_uid'),
        "appliance_type": data.get('appliance_type'),
        "brand": data.get('brand'),
        "age_years": age,
        "original_price": base_value,
        "condition_description": data.get('condition_description'),
        "estimated_value": exchange_value,
        "status": "pending",    # pending, approved, rejected
        "created_at": firestore.SERVER_TIMESTAMP
    }

    db.collection('exchanges').document(exchange_id).set(exchange)
    return jsonify({
        "message": "Exchange request submitted",
        "exchange_id": exchange_id,
        "estimated_value": exchange_value
    }), 201


# ─────────────────────────────────────────
# GET EXCHANGES (Admin or Customer)
# ─────────────────────────────────────────
@product_bp.route('/exchange/all', methods=['GET'])
def get_all_exchanges():
    try:
        exchanges = db.collection('exchanges').stream()
        return jsonify([e.to_dict() for e in exchanges]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
