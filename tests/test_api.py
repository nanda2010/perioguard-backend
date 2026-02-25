import pytest
import sys
import os
import io

# Add backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Patient, Radiograph

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for tests
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_home(client):
    rv = client.get('/')
    assert b'PerioGuard AI Backend Running' in rv.data

def test_create_patient(client):
    rv = client.post('/create_patient', json={
        'name': 'John Doe',
        'age': 30,
        'doctor': 'Dr. Smith'
    })
    json_data = rv.get_json()
    assert rv.status_code == 200
    assert 'patient_id' in json_data
    assert json_data['patient_id'] == 'P0001'

def test_get_patient(client):
    # First create
    client.post('/create_patient', json={'name': 'Jane', 'age': 40, 'doctor': 'Dr. S'})
    
    # Then get
    rv = client.get('/patient/P0001')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['name'] == 'Jane'

def test_upload_and_analyze_xray(client):
    # Create patient
    client.post('/create_patient', json={'name': 'Bob', 'age': 50, 'doctor': 'Dr. X'})
    
    # Upload X-ray (mock file)
    data = {
        'image': (io.BytesIO(b'fake image content'), 'test.jpg')
    }
    rv = client.post('/upload_xray/P0001', data=data, content_type='multipart/form-data')
    assert rv.status_code == 200
    xray_id = rv.get_json()['xray_id']
    
    # Analyze
    rv = client.get(f'/analyze_xray/{xray_id}')
    assert rv.status_code == 200
    analysis = rv.get_json()['analysis']
    assert 'gum_condition' in analysis
    assert 'recommendation' in analysis

def test_reminders_due(client):
    # Create patient (reminder defaults to +15 days, so not due)
    client.post('/create_patient', json={'name': 'Future', 'age': 20, 'doctor': 'Dr. F'})
    
    rv = client.get('/reminders_due')
    assert len(rv.get_json()['reminders_due']) == 0
    
    # TODO: Could mock datetime to test positive case, but skipping for simplicity now
