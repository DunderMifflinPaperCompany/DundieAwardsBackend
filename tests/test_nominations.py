import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.nominations.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "nominations"

def test_get_employees():
    response = client.get("/employees")
    assert response.status_code == 200
    employees = response.json()
    assert len(employees) > 0
    assert "Jim Halpert" in [emp["name"] for emp in employees]

def test_create_nomination():
    nomination_data = {
        "employee_id": "emp_001",
        "category": "Hottest in the Office",
        "nominator_id": "emp_002",
        "reason": "Jim is clearly the hottest person in Scranton"
    }
    
    response = client.post("/nominations", json=nomination_data)
    assert response.status_code == 200
    
    nomination = response.json()
    assert nomination["employee_name"] == "Jim Halpert"
    assert nomination["nominator_name"] == "Pam Beesly"
    assert nomination["category"] == "Hottest in the Office"
    assert nomination["reason"] == "Jim is clearly the hottest person in Scranton"

def test_get_nominations():
    response = client.get("/nominations")
    assert response.status_code == 200
    nominations = response.json()
    assert isinstance(nominations, list)

def test_create_nomination_invalid_employee():
    nomination_data = {
        "employee_id": "invalid_id",
        "category": "Hottest in the Office",
        "nominator_id": "emp_002",
        "reason": "Test reason"
    }
    
    response = client.post("/nominations", json=nomination_data)
    assert response.status_code == 404
    assert "Employee not found" in response.json()["detail"]