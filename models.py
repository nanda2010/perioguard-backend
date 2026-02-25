from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Patient(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    doctor_id = db.Column(db.String(100), nullable=False)
    last_checkup = db.Column(db.DateTime, default=datetime.utcnow)
    reminder_due = db.Column(db.DateTime)
    
    # Relationships
    health_data = db.relationship('HealthData', backref='patient', uselist=False, cascade="all, delete-orphan")
    radiographs = db.relationship('Radiograph', backref='patient', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "doctor": self.doctor_id,
            "last_checkup": self.last_checkup.strftime("%Y-%m-%d") if self.last_checkup else None,
            "reminder_due": self.reminder_due.strftime("%Y-%m-%d") if self.reminder_due else None,
            "health": self.health_data.to_dict() if self.health_data else None,
            "radiographs": [r.to_dict() for r in self.radiographs]
        }

class HealthData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), db.ForeignKey('patient.id'), nullable=False)
    diabetes = db.Column(db.Boolean, default=False)
    smoking = db.Column(db.Boolean, default=False)
    symptoms = db.Column(db.Text)

    def to_dict(self):
        return {
            "diabetes": self.diabetes,
            "smoking": self.smoking,
            "symptoms": self.symptoms
        }

class Radiograph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), db.ForeignKey('patient.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_result = db.Column(db.String(500)) # Storing raw JSON string or similar for simplicity

    def to_dict(self):
        return {
            "id": self.id,
            "image_path": self.image_path,
            "upload_date": self.upload_date.strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_result": self.analysis_result
        }
