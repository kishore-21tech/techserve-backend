import firebase_admin
from firebase_admin import credentials, firestore, auth

# Initialize Firebase Admin SDK
# Download your serviceAccountKey.json from Firebase Console
# Firebase Console > Project Settings > Service Accounts > Generate New Private Key

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
