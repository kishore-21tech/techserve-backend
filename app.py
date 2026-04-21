from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.technician import technician_bp
from routes.admin import admin_bp
from routes.complaint import complaint_bp
from routes.product import product_bp
import os

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(booking_bp, url_prefix='/api/booking')
app.register_blueprint(technician_bp, url_prefix='/api/technician')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(complaint_bp, url_prefix='/api/complaint')
app.register_blueprint(product_bp, url_prefix='/api/product')

@app.route('/')
def home():
    return {"message": "Customer Technician Service API Running"}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port)