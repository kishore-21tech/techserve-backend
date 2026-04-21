import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Check if running on Render (environment variable) or locally (file)
if os.environ.get('GOOGLE_CREDENTIALS'):
    # Running on Render - use environment variable
    cred_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
    cred = credentials.Certificate(cred_dict)
else:
    # Running locally - use file
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)
db = firestore.client()