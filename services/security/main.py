from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta

# Add parent directory to path for shared imports
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(services_dir)
sys.path.insert(0, root_dir)

from shared.models import AuditEvent, AuditLog, AuditEventType
from shared.utils import generate_id, get_current_timestamp
from shared.audit_utils import calculate_risk_score

app = FastAPI(title="Security/Audit Service - Dwight's Security Desk", version="1.0.0")

# In-memory storage (in production, would use a database)
audit_logs_db: Dict[str, AuditLog] = {}
processed_events: Dict[str, bool] = {}

class InvestigateRequest(BaseModel):
    investigation_notes: str

class SecurityMetrics(BaseModel):
    total_events: int
    high_risk_events: int
    investigated_events: int
    pending_investigations: int
    events_by_type: Dict[str, int]
    recent_suspicious_activity: List[AuditLog]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "security", "message": "Dwight's Security Desk is operational"}

@app.get("/audit/logs", response_model=List[AuditLog])
async def get_audit_logs(
    event_type: Optional[AuditEventType] = None,
    service_name: Optional[str] = None,
    user_id: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    investigated: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get audit logs with optional filtering"""
    logs = list(audit_logs_db.values())
    
    # Apply filters
    if event_type:
        logs = [log for log in logs if log.event_type == event_type]
    if service_name:
        logs = [log for log in logs if log.service_name == service_name]
    if user_id:
        logs = [log for log in logs if log.user_id == user_id]
    if min_risk_score is not None:
        logs = [log for log in logs if log.risk_score >= min_risk_score]
    if investigated is not None:
        logs = [log for log in logs if log.investigated == investigated]
    
    # Sort by created_at descending and limit
    logs.sort(key=lambda x: x.created_at, reverse=True)
    return logs[:limit]

@app.get("/audit/logs/{log_id}", response_model=AuditLog)
async def get_audit_log(log_id: str):
    """Get a specific audit log by ID"""
    if log_id not in audit_logs_db:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return audit_logs_db[log_id]

@app.post("/audit/logs/{log_id}/investigate")
async def investigate_audit_log(log_id: str, request: InvestigateRequest):
    """Mark an audit log as investigated with notes"""
    if log_id not in audit_logs_db:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    log = audit_logs_db[log_id]
    log.investigated = True
    log.investigation_notes = request.investigation_notes
    log.investigated_at = get_current_timestamp()
    
    return {"message": "Audit log investigated successfully", "log": log}

@app.get("/audit/suspicious", response_model=List[AuditLog])
async def get_suspicious_activity(
    min_risk_score: int = Query(50, ge=0, le=100),
    limit: int = Query(50, ge=1, le=500)
):
    """Get suspicious activities based on risk score"""
    logs = list(audit_logs_db.values())
    suspicious_logs = [log for log in logs if log.risk_score >= min_risk_score and not log.investigated]
    suspicious_logs.sort(key=lambda x: x.risk_score, reverse=True)
    return suspicious_logs[:limit]

@app.get("/audit/metrics", response_model=SecurityMetrics)
async def get_security_metrics():
    """Get security and audit metrics for Dwight's dashboard"""
    logs = list(audit_logs_db.values())
    
    # Calculate metrics
    total_events = len(logs)
    high_risk_events = len([log for log in logs if log.risk_score >= 70])
    investigated_events = len([log for log in logs if log.investigated])
    pending_investigations = len([log for log in logs if log.risk_score >= 50 and not log.investigated])
    
    # Events by type
    events_by_type = {}
    for log in logs:
        event_type = log.event_type.value
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
    
    # Recent suspicious activity (last 24 hours, risk >= 60)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_suspicious = [
        log for log in logs 
        if log.created_at >= recent_cutoff and log.risk_score >= 60
    ]
    recent_suspicious.sort(key=lambda x: x.risk_score, reverse=True)
    
    return SecurityMetrics(
        total_events=total_events,
        high_risk_events=high_risk_events,
        investigated_events=investigated_events,
        pending_investigations=pending_investigations,
        events_by_type=events_by_type,
        recent_suspicious_activity=recent_suspicious[:10]
    )

@app.delete("/audit/logs")
async def clear_audit_logs():
    """Clear all audit logs (for testing purposes)"""
    audit_logs_db.clear()
    processed_events.clear()
    return {"message": "All audit logs cleared - Dwight's desk is clean!"}

async def process_audit_event(event: AuditEvent):
    """Process a received audit event into an audit log"""
    # Skip if already processed
    if event.id in processed_events:
        return
    
    # Calculate risk score
    risk_score = calculate_risk_score(event)
    
    # Create audit log
    audit_log = AuditLog(
        id=generate_id(),
        event_id=event.id,
        event_type=event.event_type,
        service_name=event.service_name,
        user_id=event.user_id,
        user_name=event.user_name,
        details=event.details,
        risk_score=risk_score,
        investigated=False,
        created_at=event.created_at
    )
    
    # Store the audit log
    audit_logs_db[audit_log.id] = audit_log
    processed_events[event.id] = True
    
    # Log suspicious activity
    if risk_score >= 70:
        print(f"🚨 HIGH RISK ACTIVITY DETECTED: {event.event_type} (Risk: {risk_score})")
        print(f"   Service: {event.service_name}, User: {event.user_name}")
        print(f"   Details: {event.details}")

class MockAuditEventReceiver:
    """Mock receiver for development - in production would be Azure Service Bus receiver"""
    
    def __init__(self):
        self.running = False
    
    async def start_listening(self):
        """Start listening for audit events (mock implementation)"""
        self.running = True
        print("🕵️ Dwight's Security Desk is now monitoring for suspicious activity...")
        
        # In a real implementation, this would listen to Azure Service Bus
        # For now, we'll just show that the service is ready
        while self.running:
            await asyncio.sleep(5)
            # This is where we'd receive and process actual Service Bus messages
    
    def stop_listening(self):
        """Stop listening for audit events"""
        self.running = False

# Global receiver instance
_event_receiver = MockAuditEventReceiver()

@app.on_event("startup")
async def startup_event():
    """Start the audit event listener on startup"""
    # In production, you'd start the Azure Service Bus receiver here
    # For development, we'll just indicate readiness
    print("🏢 Dwight's Security Desk startup complete")
    print("📋 Ready to investigate suspicious Dundie Awards activity")
    
    # Start background listener (commented out for now as it's a mock)
    # asyncio.create_task(_event_receiver.start_listening())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    _event_receiver.stop_listening()
    print("🕵️ Dwight's Security Desk has closed for the day")

# Development endpoint to manually add test audit events
@app.post("/audit/test-event")
async def create_test_audit_event(event: AuditEvent):
    """Create a test audit event (development only)"""
    await process_audit_event(event)
    return {"message": "Test audit event processed", "event_id": event.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)