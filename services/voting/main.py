from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import sys
import os
import requests

# Add parent directory to path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import Vote, Nomination
from shared.utils import generate_id, get_current_timestamp, SAMPLE_EMPLOYEES
from shared.audit_utils import audit_vote_cast

app = FastAPI(title="Voting Service", version="1.0.0")

# In-memory storage
votes_db: Dict[str, Vote] = {}

# Service configuration
NOMINATIONS_SERVICE_URL = os.getenv("NOMINATIONS_SERVICE_URL", "http://localhost:8001")

class CreateVoteRequest(BaseModel):
    nomination_id: str
    voter_id: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voting"}

@app.post("/votes", response_model=Vote)
async def create_vote(request: CreateVoteRequest):
    """Cast a vote for a nomination"""
    # Verify nomination exists
    try:
        response = requests.get(f"{NOMINATIONS_SERVICE_URL}/nominations/{request.nomination_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Nomination not found")
        nomination_data = response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Unable to verify nomination")
    
    # Find voter
    voter = next((emp for emp in SAMPLE_EMPLOYEES if emp["id"] == request.voter_id), None)
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")
    
    # Check if voter has already voted for this nomination
    existing_vote = next((v for v in votes_db.values() 
                         if v.nomination_id == request.nomination_id and v.voter_id == request.voter_id), None)
    if existing_vote:
        raise HTTPException(status_code=400, detail="Voter has already voted for this nomination")
    
    # Create vote
    vote = Vote(
        id=generate_id(),
        nomination_id=request.nomination_id,
        voter_id=request.voter_id,
        voter_name=voter["name"],
        created_at=get_current_timestamp()
    )
    
    votes_db[vote.id] = vote
    
    # Emit audit event
    try:
        await audit_vote_cast(
            voter_id=vote.voter_id,
            voter_name=vote.voter_name,
            nomination_id=vote.nomination_id,
            vote_id=vote.id
        )
    except Exception as e:
        # Don't let audit failures break the vote
        print(f"Failed to emit audit event: {e}")
    
    return vote

@app.get("/votes", response_model=List[Vote])
async def get_votes(nomination_id: str = None):
    """Get all votes, optionally filtered by nomination"""
    votes = list(votes_db.values())
    if nomination_id:
        votes = [v for v in votes if v.nomination_id == nomination_id]
    return votes

@app.get("/votes/count/{nomination_id}")
async def get_vote_count(nomination_id: str):
    """Get vote count for a specific nomination"""
    count = len([v for v in votes_db.values() if v.nomination_id == nomination_id])
    return {"nomination_id": nomination_id, "vote_count": count}

@app.get("/votes/results")
async def get_voting_results():
    """Get voting results grouped by nomination"""
    results = {}
    for vote in votes_db.values():
        if vote.nomination_id not in results:
            results[vote.nomination_id] = {
                "nomination_id": vote.nomination_id,
                "vote_count": 0,
                "voters": []
            }
        results[vote.nomination_id]["vote_count"] += 1
        results[vote.nomination_id]["voters"].append(vote.voter_name)
    
    return list(results.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)