from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from models import db, Patient, HealthData, Radiograph
from ai_engine import MedicalAI
import json

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'perioguard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)

# Upload folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "PerioGuard AI Backend Running (SQLite Persistence Enabled)"

# Doctor creates patient ID
@app.route("/create_patient", methods=["POST"])
def create_patient():
    data = request.json
    
    # Generate simple ID P0001, P0002 based on count for now
    count = Patient.query.count()
    patient_id = f"P{count + 1:04d}"
    
    new_patient = Patient(
        id=patient_id,
        name=data.get("name"),
        age=data.get("age"),
        doctor_id=data.get("doctor"),
        last_checkup=datetime.now(),
        reminder_due=datetime.now() + timedelta(days=15)
    )
    
    db.session.add(new_patient)
    db.session.commit()
    
    return jsonify({
        "message": "Patient created",
        "patient_id": patient_id
    })

# Check patient exists
@app.route("/patient/<patient_id>")
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if patient:
        return jsonify(patient.to_dict())
    return jsonify({"error": "Patient not found"}), 404

# Add patient health data
@app.route("/add_health/<patient_id>", methods=["POST"])
def add_health(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    data = request.json
    
    # Update or create health data
    if patient.health_data:
        patient.health_data.diabetes = data.get("diabetes")
        patient.health_data.smoking = data.get("smoking")
        patient.health_data.symptoms = data.get("symptoms")
    else:
        health = HealthData(
            patient_id=patient_id,
            diabetes=data.get("diabetes"),
            smoking=data.get("smoking"),
            symptoms=data.get("symptoms")
        )
        db.session.add(health)
    
    db.session.commit()
    return jsonify({"message": "Health data updated"})

# Upload radiograph
@app.route("/upload_xray/<patient_id>", methods=["POST"])
def upload_xray(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
        
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
        
    file = request.files["image"]
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(f"{patient_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    
    # Create Radiograph record
    xray = Radiograph(
        patient_id=patient_id,
        image_path=path,
        analysis_result="Pending" 
    )
    db.session.add(xray)
    db.session.commit()
    
    return jsonify({
        "message": "X-ray uploaded successfully",
        "xray_id": xray.id
    })

# Analyze X-ray using AI Engine
@app.route("/analyze_xray/<int:xray_id>", methods=["GET"])
def analyze_xray(xray_id):
    xray = Radiograph.query.get(xray_id)
    if not xray:
        return jsonify({"error": "Radiograph not found"}), 404
        
    # Perform analysis
    analysis = MedicalAI.analyze_image(xray.image_path)
    
    # Update DB with result
    xray.analysis_result = json.dumps(analysis)
    db.session.commit()
    
    return jsonify({
        "patient_id": xray.patient_id,
        "xray_id": xray.id,
        "analysis": analysis
    })

# Reminder check
@app.route("/reminders_due", methods=["GET"])
def reminders_due():
    today = datetime.now()
    # Find patients where reminder_due is in the past or today
    patients_due = Patient.query.filter(Patient.reminder_due <= today).all()
    
    due_list = []
    for p in patients_due:
        due_list.append({
            "patient_id": p.id,
            "name": p.name,
            "doctor": p.doctor_id,
            "last_checkup": p.last_checkup.strftime("%Y-%m-%d") if p.last_checkup else "N/A",
            "reminder_due": p.reminder_due.strftime("%Y-%m-%d") if p.reminder_due else "N/A"
        })
        
    return jsonify({"reminders_due": due_list})

# Mock Login for Demo
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("pass") # matching android model field name 'pass'
    
    # Simple hardcoded check for demo
    if email == "doctor@perioguard.ai" and password == "doctor123":
        return jsonify({
            "token": "mock_doctor_token_123",
            "role": "doctor",
            "id": "DOC001",
            "name": "Dr. Sarah Smith",
            "email": "doctor@perioguard.ai"
        })
    elif email == "patient@perioguard.ai" and password == "patient123":
         return jsonify({
            "token": "mock_patient_token_456",
            "role": "patient",
            "id": "P0001",
            "name": "James Wilson",
            "email": "patient@perioguard.ai"
        })
    
    return jsonify({"error": "Invalid credentials"}), 401


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)