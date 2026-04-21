from flask import Blueprint, request, jsonify
from firebase_config import db
from firebase_admin import firestore
import uuid
from datetime import datetime

booking_bp = Blueprint('booking', __name__)

# ─────────────────────────────────────────
# CREATE BOOKING
# ─────────────────────────────────────────
@booking_bp.route('/create', methods=['POST'])
def create_booking():
    data = request.json
    booking_id = str(uuid.uuid4())

    booking = {
        "booking_id": booking_id,
        "customer_uid": data.get('customer_uid'),
        "customer_name": data.get('customer_name'),
        "appliance_type": data.get('appliance_type'),  # e.g. AC, Washing Machine
        "issue_description": data.get('issue_description'),
        "address": data.get('address'),
        "location": data.get('location'),  # {lat, lng}
        "date": data.get('date'),
        "time_slot": data.get('time_slot'),
        "status": "pending",              # pending > assigned > in_progress > completed
        "technician_uid": None,
        "technician_name": None,
        "created_at": firestore.SERVER_TIMESTAMP
    }

    db.collection('bookings').document(booking_id).set(booking)

    # Auto-assign technician based on appliance type
    assigned = auto_assign_technician(booking_id, data.get('appliance_type'), data.get('location'))

    return jsonify({
        "message": "Booking created",
        "booking_id": booking_id,
        "assigned_technician": assigned
    }), 201


# ─────────────────────────────────────────
# AUTO-ASSIGN TECHNICIAN
# ─────────────────────────────────────────
def auto_assign_technician(booking_id, appliance_type, customer_location):
    try:
        techs = db.collection('users').where('role', '==', 'technician')\
                                       .where('status', '==', 'online').stream()

        best_tech = None
        for tech in techs:
            t = tech.to_dict()
            expertise = t.get('appliance_expertise', [])
            if appliance_type in expertise:
                best_tech = t
                break

        if best_tech:
            db.collection('bookings').document(booking_id).update({
                "technician_uid": best_tech['uid'],
                "technician_name": best_tech['name'],
                "status": "assigned"
            })
            # Notify technician (via Firebase notification in real app)
            return {"name": best_tech['name'], "uid": best_tech['uid']}
        return None
    except Exception as e:
        return None


# ─────────────────────────────────────────
# GET BOOKINGS FOR CUSTOMER
# ─────────────────────────────────────────
@booking_bp.route('/customer/<uid>', methods=['GET'])
def get_customer_bookings(uid):
    try:
        bookings = db.collection('bookings').where('customer_uid', '==', uid).stream()
        result = [b.to_dict() for b in bookings]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# GET BOOKINGS FOR TECHNICIAN
# ─────────────────────────────────────────
@booking_bp.route('/technician/<uid>', methods=['GET'])
def get_technician_bookings(uid):
    try:
        bookings = db.collection('bookings').where('technician_uid', '==', uid).stream()
        result = [b.to_dict() for b in bookings]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# UPDATE BOOKING STATUS
# ─────────────────────────────────────────
@booking_bp.route('/status/<booking_id>', methods=['PUT'])
def update_status(booking_id):
    data = request.json
    status = data.get('status')  # assigned, in_progress, completed, cancelled
    try:
        db.collection('bookings').document(booking_id).update({"status": status})
        return jsonify({"message": f"Status updated to {status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# GET ALL BOOKINGS (Admin)
# ─────────────────────────────────────────
@booking_bp.route('/all', methods=['GET'])
def get_all_bookings():
    try:
        bookings = db.collection('bookings').stream()
        result = [b.to_dict() for b in bookings]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
