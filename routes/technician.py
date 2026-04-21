from flask import Blueprint, request, jsonify
from firebase_config import db
from firebase_admin import firestore

technician_bp = Blueprint('technician', __name__)

# ─────────────────────────────────────────
# UPDATE TECHNICIAN STATUS (online/offline)
# ─────────────────────────────────────────
@technician_bp.route('/status/<uid>', methods=['PUT'])
def update_status(uid):
    data = request.json
    status = data.get('status')  # 'online' or 'offline'
    try:
        db.collection('users').document(uid).update({"status": status})
        return jsonify({"message": f"Status set to {status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# UPDATE TECHNICIAN LIVE LOCATION
# ─────────────────────────────────────────
@technician_bp.route('/location/<uid>', methods=['PUT'])
def update_location(uid):
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    try:
        db.collection('users').document(uid).update({
            "location": {"lat": lat, "lng": lng}
        })
        return jsonify({"message": "Location updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# GET TECHNICIAN LIVE LOCATION (for tracking)
# ─────────────────────────────────────────
@technician_bp.route('/location/<uid>', methods=['GET'])
def get_location(uid):
    try:
        doc = db.collection('users').document(uid).get()
        if not doc.exists:
            return jsonify({"error": "Technician not found"}), 404
        data = doc.to_dict()
        return jsonify({"location": data.get('location', {})}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# SUBMIT RATING FOR TECHNICIAN
# ─────────────────────────────────────────
@technician_bp.route('/rate', methods=['POST'])
def rate_technician():
    data = request.json
    booking_id = data.get('booking_id')
    technician_uid = data.get('technician_uid')
    customer_uid = data.get('customer_uid')
    stars = data.get('stars')       # 1 to 5
    comment = data.get('comment', '')

    try:
        # Save the review
        review = {
            "booking_id": booking_id,
            "technician_uid": technician_uid,
            "customer_uid": customer_uid,
            "stars": stars,
            "comment": comment,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        db.collection('reviews').add(review)

        # Recalculate average rating for technician
        reviews = db.collection('reviews').where('technician_uid', '==', technician_uid).stream()
        all_stars = [r.to_dict().get('stars', 0) for r in reviews]
        avg = round(sum(all_stars) / len(all_stars), 1) if all_stars else 0

        db.collection('users').document(technician_uid).update({
            "rating": avg,
            "total_reviews": len(all_stars)
        })

        # Mark booking as rated
        db.collection('bookings').document(booking_id).update({"rated": True})

        return jsonify({"message": "Rating submitted", "new_avg": avg}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# GET ALL TECHNICIANS
# ─────────────────────────────────────────
@technician_bp.route('/all', methods=['GET'])
def get_all_technicians():
    try:
        techs = db.collection('users').where('role', '==', 'technician').stream()
        result = [t.to_dict() for t in techs]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# GET REVIEWS FOR TECHNICIAN
# ─────────────────────────────────────────
@technician_bp.route('/reviews/<uid>', methods=['GET'])
def get_reviews(uid):
    try:
        reviews = db.collection('reviews').where('technician_uid', '==', uid).stream()
        result = [r.to_dict() for r in reviews]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
