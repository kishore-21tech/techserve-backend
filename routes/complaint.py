from flask import Blueprint, request, jsonify
from firebase_config import db
from firebase_admin import firestore
import uuid

complaint_bp = Blueprint('complaint', __name__)

# ─────────────────────────────────────────
# SUBMIT COMPLAINT
# ─────────────────────────────────────────
@complaint_bp.route('/submit', methods=['POST'])
def submit_complaint():
    data = request.json
    complaint_id = str(uuid.uuid4())

    complaint = {
        "complaint_id": complaint_id,
        "customer_uid": data.get('customer_uid'),
        "customer_name": data.get('customer_name'),
        "booking_id": data.get('booking_id'),
        "technician_uid": data.get('technician_uid'),
        "description": data.get('description'),
        "priority": "normal",     # normal, high, urgent
        "status": "open",         # open, under_review, resolved
        "created_at": firestore.SERVER_TIMESTAMP
    }

    db.collection('complaints').document(complaint_id).set(complaint)
    return jsonify({"message": "Complaint submitted", "complaint_id": complaint_id}), 201


# ─────────────────────────────────────────
# GET ALL COMPLAINTS (Admin)
# ─────────────────────────────────────────
@complaint_bp.route('/all', methods=['GET'])
def get_all_complaints():
    try:
        complaints = db.collection('complaints').stream()
        result = [c.to_dict() for c in complaints]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# GET COMPLAINTS FOR CUSTOMER
# ─────────────────────────────────────────
@complaint_bp.route('/customer/<uid>', methods=['GET'])
def get_customer_complaints(uid):
    try:
        complaints = db.collection('complaints').where('customer_uid', '==', uid).stream()
        result = [c.to_dict() for c in complaints]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# UPDATE COMPLAINT PRIORITY & STATUS (Admin)
# ─────────────────────────────────────────
@complaint_bp.route('/update/<complaint_id>', methods=['PUT'])
def update_complaint(complaint_id):
    data = request.json
    try:
        db.collection('complaints').document(complaint_id).update(data)
        return jsonify({"message": "Complaint updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
