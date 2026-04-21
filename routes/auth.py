from flask import Blueprint, request, jsonify
from firebase_config import db
from firebase_admin import auth as firebase_auth
import requests as http_requests

auth_bp = Blueprint('auth', __name__)
FIREBASE_WEB_API_KEY = "AIzaSyAFIvgVbFAVvy9xCphCAhVVr1re1pI3-Sc"

# ── Only this email can be admin ──────────────────────────
ADMIN_EMAIL = "admin@techserve.com"
# ─────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', 'customer')
    phone = data.get('phone', '')

    # Block anyone from registering as admin
    if role == 'admin':
        return jsonify({"error": "Unauthorized. Admin registration is not allowed."}), 403

    if role not in ['customer', 'technician']:
        return jsonify({"error": "Invalid role"}), 400

    try:
        user = firebase_auth.create_user(email=email, password=password, display_name=name)
        user_data = {"uid": user.uid, "name": name, "email": email, "role": role, "phone": phone}

        if role == 'technician':
            user_data["status"] = "offline"
            user_data["appliance_expertise"] = data.get('appliance_expertise', [])
            user_data["location"] = {"lat": 0.0, "lng": 0.0}
            user_data["rating"] = 0.0
            user_data["total_jobs"] = 0

        db.collection('users').document(user.uid).set(user_data)
        return jsonify({"message": "User registered successfully", "uid": user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        firebase_response = http_requests.post(firebase_url, json={
            "email": email, "password": password, "returnSecureToken": True
        })
        firebase_data = firebase_response.json()

        if 'error' in firebase_data:
            error_msg = firebase_data['error'].get('message', 'Login failed')
            if 'INVALID_PASSWORD' in error_msg or 'INVALID_LOGIN_CREDENTIALS' in error_msg:
                return jsonify({"error": "Wrong password. Please try again."}), 401
            elif 'EMAIL_NOT_FOUND' in error_msg:
                return jsonify({"error": "Email not found. Please register first."}), 404
            else:
                return jsonify({"error": error_msg}), 401

        uid = firebase_data.get('localId')
        user_doc = db.collection('users').document(uid).get()

        # If admin email logs in but no profile exists, auto create admin profile
        if not user_doc.exists and email == ADMIN_EMAIL:
            admin_data = {
                "uid": uid, "name": "Admin", "email": email,
                "role": "admin", "phone": ""
            }
            db.collection('users').document(uid).set(admin_data)
            return jsonify({
                "message": "Login successful", "uid": uid,
                "name": "Admin", "email": email, "role": "admin",
                "phone": "", "status": "", "appliance_expertise": [], "rating": 0
            }), 200

        if not user_doc.exists:
            return jsonify({"error": "User profile not found. Please register again."}), 404

        user_data = user_doc.to_dict()
        return jsonify({
            "message": "Login successful",
            "uid": uid,
            "name": user_data.get('name'),
            "email": user_data.get('email'),
            "role": user_data.get('role'),
            "phone": user_data.get('phone', ''),
            "status": user_data.get('status', ''),
            "appliance_expertise": user_data.get('appliance_expertise', []),
            "rating": user_data.get('rating', 0),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    try:
        firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        firebase_response = http_requests.post(firebase_url, json={
            "requestType": "PASSWORD_RESET", "email": email
        })
        firebase_data = firebase_response.json()
        if 'error' in firebase_data:
            error_msg = firebase_data['error'].get('message', 'Failed')
            if 'EMAIL_NOT_FOUND' in error_msg:
                return jsonify({"error": "Email not registered."}), 404
            return jsonify({"error": error_msg}), 400
        return jsonify({"message": "Password reset email sent!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/profile/<uid>', methods=['GET'])
def get_profile(uid):
    try:
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user_doc.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/profile/<uid>', methods=['PUT'])
def update_profile(uid):
    data = request.json
    try:
        db.collection('users').document(uid).update(data)
        return jsonify({"message": "Profile updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500