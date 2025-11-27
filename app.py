import os
import json
import re
import random
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-' + os.urandom(16).hex())

CORS(app, supports_credentials=True, origins=["*"])

JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-' + os.urandom(16).hex())

TOKEN_EXPIRY_HOURS = 24

users_db = {}
password_reset_tokens_db = {}

# Updated House Plans database with multiple square foot entries per BHK
HOUSE_PLANS = {
    "1bhk": {
        "400": {
            "filename": "1bhk-400.jpg",
            "description": "Compact 1BHK with efficient space utilization"
        },
        "500": {
            "filename": "1bhk-500.jpg",
            "description": "Spacious 1BHK with balcony"
        },
        "520":{
            "filename": "1bhk-520.jpg"
        },
        "625": {
            "filename": "1bhk-625.jpg",
            "description": "Modern 1BHK with extra storage"
        }
    },
    "2bhk": {
        "500": {
            "filename": "2bhk-500.jpg",
            "description": "Modern 2BHK with open kitchen"
        },
        "700": {
            "filename": "2bhk-700.jpg",
            "description": "Cozy 2BHK with spacious living room"
        }
    },
    "3bhk": {
        "900": {
            "filename": "3bhk-900.jpg",
            "description": "Luxury 3BHK with master suite"
        },
        "1100": {
            "filename": "3bhk-1100.jpg",
            "description": "3BHK with balcony and garden view"
        }
    }
}

HOUSEPLANS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "houseplans")

# Helper Functions (token management and auth checks unchanged, omitted here for brevity)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = auth_header.split()[1]
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user = users_db.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except Exception:
            return jsonify({'error': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/houseplans/<filename>')
def serve_houseplan(filename):
    return send_from_directory(HOUSEPLANS_FOLDER, filename)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/get-plan', methods=['POST'])
def get_plan():
    try:
        data = request.get_json()
        square_footage = str(data.get('square_footage', "")).strip()
        bedrooms = data.get('bedrooms', "")
        bhk = f"{bedrooms}bhk"

        # Validate inputs
        if not bhk or not square_footage:
            return jsonify({"error": "Invalid request parameters"}), 400

        # Check if exact plan exists for requested BHK and square footage
        if bhk in HOUSE_PLANS and square_footage in HOUSE_PLANS[bhk]:
            plan_data = HOUSE_PLANS[bhk][square_footage]
            filename = plan_data.get("filename", "")
            file_path = os.path.join(HOUSEPLANS_FOLDER, filename)

            # Check if the file actually exists
            if not os.path.isfile(file_path):
                return jsonify({"error": f"No house plan available for {bhk} with {square_footage} sq ft"}), 404

            image_url = f"/houseplans/{filename}"
            return jsonify({
                "success": True,
                "bhk": bhk,
                "size": square_footage,
                "requested_size": square_footage,
                "image_url": image_url,
                "direct_link": image_url,
                "description": plan_data.get("description", "")
            })
        else:
            # No exact match found
            return jsonify({"error": f"No house plan available for {bhk} with {square_footage} sq ft"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# (Other API routes for login, register, forgot/reset password, user info unchanged - use previous code)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
