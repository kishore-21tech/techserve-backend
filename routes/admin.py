from flask import Blueprint, request, jsonify
from firebase_config import db

admin_bp = Blueprint('admin', __name__)

# ─────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────
@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        customers = list(db.collection('users').where('role', '==', 'customer').stream())
        technicians = list(db.collection('users').where('role', '==', 'technician').stream())
        bookings = list(db.collection('bookings').stream())
        complaints = list(db.collection('complaints').stream())

        pending = [b for b in bookings if b.to_dict().get('status') == 'pending']
        completed = [b for b in bookings if b.to_dict().get('status') == 'completed']

        return jsonify({
            "total_customers": len(customers),
            "total_technicians": len(technicians),
            "total_bookings": len(bookings),
            "pending_bookings": len(pending),
            "completed_bookings": len(completed),
            "total_complaints": len(complaints)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# ASSIGN TECHNICIAN MANUALLY
# ─────────────────────────────────────────
@admin_bp.route('/assign', methods=['POST'])
def assign_technician():
    data = request.json
    booking_id = data.get('booking_id')
    technician_uid = data.get('technician_uid')
    technician_name = data.get('technician_name')

    try:
        db.collection('bookings').document(booking_id).update({
            "technician_uid": technician_uid,
            "technician_name": technician_name,
            "status": "assigned"
        })
        return jsonify({"message": "Technician assigned manually"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# REPORTS - Most repaired appliances
# ─────────────────────────────────────────
@admin_bp.route('/reports/appliances', methods=['GET'])
def appliance_report():
    try:
        bookings = db.collection('bookings').stream()
        count = {}
        for b in bookings:
            appliance = b.to_dict().get('appliance_type', 'Unknown')
            count[appliance] = count.get(appliance, 0) + 1
        sorted_result = sorted(count.items(), key=lambda x: x[1], reverse=True)
        return jsonify(sorted_result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# REPORTS - Technician performance
# ─────────────────────────────────────────
@admin_bp.route('/reports/technicians', methods=['GET'])
def technician_performance():
    try:
        techs = db.collection('users').where('role', '==', 'technician').stream()
        result = []
        for t in techs:
            tech = t.to_dict()
            completed = list(db.collection('bookings')
                               .where('technician_uid', '==', tech['uid'])
                               .where('status', '==', 'completed').stream())
            result.append({
                "name": tech.get('name'),
                "uid": tech.get('uid'),
                "rating": tech.get('rating', 0),
                "completed_jobs": len(completed)
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# DELETE USER (admin only)
# ─────────────────────────────────────────
@admin_bp.route('/user/<uid>', methods=['DELETE'])
def delete_user(uid):
    try:
        db.collection('users').document(uid).delete()
        return jsonify({"message": "User deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
