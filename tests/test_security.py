import sys
import os
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.security.main import app
from shared.models import AuditEvent, AuditEventType

client = TestClient(app)

def test_health_check():
    """Test security service health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "security"
    assert "Dwight's Security Desk" in data["message"]

def test_get_audit_logs_empty():
    """Test getting audit logs when none exist"""
    # Clear any existing logs
    client.delete("/audit/logs")
    
    response = client.get("/audit/logs")
    assert response.status_code == 200
    assert response.json() == []

def test_create_test_audit_event():
    """Test creating a test audit event"""
    # Clear any existing logs
    client.delete("/audit/logs")
    
    event_data = {
        "id": "test-event-1",
        "event_type": "nomination_submitted",
        "service_name": "nominations",
        "user_id": "emp_001",
        "user_name": "Jim Halpert",
        "resource_id": "nom_001",
        "resource_type": "nomination",
        "details": {
            "category": "Hottest in the Office",
            "employee_id": "emp_002"
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    response = client.post("/audit/test-event", json=event_data)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "test-event-1"
    
    # Verify the audit log was created
    logs_response = client.get("/audit/logs")
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert len(logs) == 1
    assert logs[0]["event_id"] == "test-event-1"
    assert logs[0]["service_name"] == "nominations"
    assert logs[0]["user_name"] == "Jim Halpert"

def test_get_security_metrics():
    """Test getting security metrics"""
    # Clear any existing logs
    client.delete("/audit/logs")
    
    response = client.get("/audit/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data
    assert "high_risk_events" in data
    assert "investigated_events" in data
    assert "pending_investigations" in data
    assert "events_by_type" in data
    assert "recent_suspicious_activity" in data

def test_investigate_audit_log():
    """Test investigating an audit log"""
    # Clear any existing logs
    client.delete("/audit/logs")
    
    # Create a test event first
    event_data = {
        "id": "test-event-2",
        "event_type": "vote_cast",
        "service_name": "voting",
        "user_id": "emp_003",
        "user_name": "Dwight Schrute",
        "details": {"suspicious": "multiple rapid votes"},
        "created_at": datetime.utcnow().isoformat()
    }
    
    client.post("/audit/test-event", json=event_data)
    
    # Get the logs to find the log ID
    logs_response = client.get("/audit/logs")
    logs = logs_response.json()
    log_id = logs[0]["id"]
    
    # Investigate the log
    investigation_data = {
        "investigation_notes": "Investigated by Dwight. False alarm - legitimate voting pattern."
    }
    
    response = client.post(f"/audit/logs/{log_id}/investigate", json=investigation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Audit log investigated successfully"
    assert data["log"]["investigated"] == True
    assert data["log"]["investigation_notes"] == investigation_data["investigation_notes"]

def test_get_suspicious_activity():
    """Test getting suspicious activity"""
    # Clear any existing logs
    client.delete("/audit/logs")
    
    # Create a high-risk test event
    event_data = {
        "id": "test-event-3",
        "event_type": "suspicious_activity",
        "service_name": "security",
        "details": {"alert": "multiple failed attempts"},
        "created_at": datetime.utcnow().isoformat()
    }
    
    client.post("/audit/test-event", json=event_data)
    
    response = client.get("/audit/suspicious?min_risk_score=70")
    assert response.status_code == 200
    suspicious_logs = response.json()
    assert len(suspicious_logs) >= 1

def test_audit_log_filters():
    """Test filtering audit logs"""
    # Clear any existing logs
    client.delete("/audit/logs")
    
    # Create test events
    events = [
        {
            "id": "test-event-4",
            "event_type": "nomination_submitted",
            "service_name": "nominations",
            "user_id": "emp_001",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "test-event-5", 
            "event_type": "vote_cast",
            "service_name": "voting",
            "user_id": "emp_002",
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    for event in events:
        client.post("/audit/test-event", json=event)
    
    # Test filtering by service
    response = client.get("/audit/logs?service_name=nominations")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["service_name"] == "nominations"
    
    # Test filtering by user
    response = client.get("/audit/logs?user_id=emp_002")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["user_id"] == "emp_002"
    
    # Test filtering by event type
    response = client.get("/audit/logs?event_type=vote_cast")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["event_type"] == "vote_cast"