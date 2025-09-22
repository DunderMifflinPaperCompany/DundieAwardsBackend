from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import sys
import os
import requests
from collections import defaultdict

# Add parent directory to path for shared imports
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(services_dir)
sys.path.insert(0, root_dir)

from shared.models import Winner, AwardCategory
from shared.utils import generate_id, get_current_timestamp
from shared.audit_utils import audit_winner_calculated

app = FastAPI(title="Winners Service", version="1.0.0")

# In-memory storage
winners_db: Dict[str, Winner] = {}

# Service configuration
NOMINATIONS_SERVICE_URL = os.getenv("NOMINATIONS_SERVICE_URL", "http://localhost:8001")
VOTING_SERVICE_URL = os.getenv("VOTING_SERVICE_URL", "http://localhost:8002")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "winners"}

@app.post("/winners/calculate")
async def calculate_winners():
    """Calculate winners based on current votes"""
    try:
        # Get all nominations
        nominations_response = requests.get(f"{NOMINATIONS_SERVICE_URL}/nominations")
        if nominations_response.status_code != 200:
            raise HTTPException(status_code=503, detail="Unable to fetch nominations")
        nominations = nominations_response.json()
        
        # Get voting results
        votes_response = requests.get(f"{VOTING_SERVICE_URL}/votes/results")
        if votes_response.status_code != 200:
            raise HTTPException(status_code=503, detail="Unable to fetch voting results")
        vote_results = votes_response.json()
        
        # Create a mapping of nomination_id to vote count
        vote_counts = {result["nomination_id"]: result["vote_count"] for result in vote_results}
        
        # Group nominations by category and find winner for each
        category_nominations = defaultdict(list)
        for nomination in nominations:
            category_nominations[nomination["category"]].append(nomination)
        
        new_winners = []
        
        for category, category_noms in category_nominations.items():
            # Find nomination with highest votes in this category
            best_nomination = None
            highest_votes = -1
            
            for nomination in category_noms:
                vote_count = vote_counts.get(nomination["id"], 0)
                if vote_count > highest_votes:
                    highest_votes = vote_count
                    best_nomination = nomination
            
            if best_nomination and highest_votes > 0:
                # Create winner entry
                winner = Winner(
                    id=generate_id(),
                    nomination_id=best_nomination["id"],
                    employee_id=best_nomination["employee_id"],
                    employee_name=best_nomination["employee_name"],
                    category=AwardCategory(best_nomination["category"]),
                    total_votes=highest_votes,
                    reason=best_nomination["reason"],
                    created_at=get_current_timestamp()
                )
                
                # Store winner (replace if already exists for this category)
                existing_winner = next((w for w in winners_db.values() 
                                      if w.category == winner.category), None)
                if existing_winner:
                    del winners_db[existing_winner.id]
                
                winners_db[winner.id] = winner
                new_winners.append(winner)
                
                # Emit audit event
                try:
                    await audit_winner_calculated(
                        category=winner.category.value,
                        winner_id=winner.id,
                        total_votes=winner.total_votes
                    )
                except Exception as e:
                    # Don't let audit failures break the winner calculation
                    print(f"Failed to emit audit event: {e}")
        
        return {"message": f"Calculated {len(new_winners)} winners", "winners": new_winners}
        
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Service communication error: {str(e)}")

@app.get("/winners", response_model=List[Winner])
async def get_winners(category: AwardCategory = None):
    """Get all winners, optionally filtered by category"""
    winners = list(winners_db.values())
    if category:
        winners = [w for w in winners if w.category == category]
    return winners

@app.get("/winners/{winner_id}", response_model=Winner)
async def get_winner(winner_id: str):
    """Get a specific winner by ID"""
    if winner_id not in winners_db:
        raise HTTPException(status_code=404, detail="Winner not found")
    return winners_db[winner_id]

@app.delete("/winners")
async def clear_winners():
    """Clear all winners (for testing purposes)"""
    winners_db.clear()
    return {"message": "All winners cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)