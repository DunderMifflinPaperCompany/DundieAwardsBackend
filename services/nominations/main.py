from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import sys
import os

# Add parent directory to path for shared imports
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(services_dir)
sys.path.insert(0, root_dir)

from shared.models import Nomination, AwardCategory
from shared.utils import generate_id, get_current_timestamp, SAMPLE_EMPLOYEES
from shared.audit_utils import audit_nomination_submitted

app = FastAPI(title="Nominations Service", version="1.0.0")

# In-memory storage (in production, would use a database)
nominations_db: Dict[str, Nomination] = {}

class CreateNominationRequest(BaseModel):
    employee_id: str
    category: AwardCategory
    nominator_id: str
    reason: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nominations"}

@app.get("/employees")
async def get_employees():
    """Get list of employees that can be nominated"""
    return SAMPLE_EMPLOYEES

@app.post("/nominations", response_model=Nomination)
async def create_nomination(request: CreateNominationRequest):
    """Create a new nomination"""
    # Find employee and nominator names
    employee = next((emp for emp in SAMPLE_EMPLOYEES if emp["id"] == request.employee_id), None)
    nominator = next((emp for emp in SAMPLE_EMPLOYEES if emp["id"] == request.nominator_id), None)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not nominator:
        raise HTTPException(status_code=404, detail="Nominator not found")
    
    # Create nomination
    nomination = Nomination(
        id=generate_id(),
        employee_id=request.employee_id,
        employee_name=employee["name"],
        category=request.category,
        nominator_id=request.nominator_id,
        nominator_name=nominator["name"],
        reason=request.reason,
        created_at=get_current_timestamp()
    )
    
    nominations_db[nomination.id] = nomination
    
    # Emit audit event
    try:
        await audit_nomination_submitted(
            nominator_id=nomination.nominator_id,
            nominator_name=nomination.nominator_name,
            employee_id=nomination.employee_id,
            category=nomination.category.value,
            nomination_id=nomination.id
        )
    except Exception as e:
        # Don't let audit failures break the nomination
        print(f"Failed to emit audit event: {e}")
    
    return nomination

@app.get("/nominations", response_model=List[Nomination])
async def get_nominations(category: AwardCategory = None):
    """Get all nominations, optionally filtered by category"""
    nominations = list(nominations_db.values())
    if category:
        nominations = [n for n in nominations if n.category == category]
    return nominations

@app.get("/nominations/{nomination_id}", response_model=Nomination)
async def get_nomination(nomination_id: str):
    """Get a specific nomination by ID"""
    if nomination_id not in nominations_db:
        raise HTTPException(status_code=404, detail="Nomination not found")
    return nominations_db[nomination_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)