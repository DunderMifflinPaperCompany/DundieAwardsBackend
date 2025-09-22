from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import sys
import os
import requests

# Add parent directory to path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import Notification
from shared.utils import generate_id, get_current_timestamp
from shared.audit_utils import audit_notification_sent

app = FastAPI(title="Notifications Service", version="1.0.0")

# In-memory storage
notifications_db: Dict[str, Notification] = {}

# Service configuration
WINNERS_SERVICE_URL = os.getenv("WINNERS_SERVICE_URL", "http://localhost:8003")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notifications"}

@app.post("/notifications/send")
async def send_notifications():
    """Send notifications to all current winners"""
    try:
        # Get all winners
        winners_response = requests.get(f"{WINNERS_SERVICE_URL}/winners")
        if winners_response.status_code != 200:
            raise HTTPException(status_code=503, detail="Unable to fetch winners")
        winners = winners_response.json()
        
        new_notifications = []
        
        for winner in winners:
            # Check if notification already sent for this winner
            existing_notification = next((n for n in notifications_db.values() 
                                        if n.winner_id == winner["id"]), None)
            if existing_notification:
                continue
            
            # Create congratulatory message
            message = f"""🏆 Congratulations {winner['employee_name']}! 

You've won the Dundie Award for '{winner['category']}' with {winner['total_votes']} votes!

Reason: {winner['reason']}

Your award ceremony will be held at Chili's at 7 PM. Drinks are on Michael Scott!

- The Dundie Awards Committee"""
            
            # Create notification
            notification = Notification(
                id=generate_id(),
                winner_id=winner["id"],
                employee_id=winner["employee_id"],
                employee_name=winner["employee_name"],
                category=winner["category"],
                message=message,
                sent=True,  # In real implementation, would send email/SMS here
                created_at=get_current_timestamp()
            )
            
            notifications_db[notification.id] = notification
            new_notifications.append(notification)
            
            # Emit audit event
            try:
                await audit_notification_sent(
                    winner_id=notification.winner_id,
                    employee_id=notification.employee_id,
                    employee_name=notification.employee_name,
                    notification_id=notification.id
                )
            except Exception as e:
                # Don't let audit failures break the notification
                print(f"Failed to emit audit event: {e}")
        
        return {
            "message": f"Sent {len(new_notifications)} notifications", 
            "notifications": new_notifications
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Service communication error: {str(e)}")

@app.get("/notifications", response_model=List[Notification])
async def get_notifications(employee_id: str = None):
    """Get all notifications, optionally filtered by employee"""
    notifications = list(notifications_db.values())
    if employee_id:
        notifications = [n for n in notifications if n.employee_id == employee_id]
    return notifications

@app.get("/notifications/{notification_id}", response_model=Notification)
async def get_notification(notification_id: str):
    """Get a specific notification by ID"""
    if notification_id not in notifications_db:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notifications_db[notification_id]

@app.delete("/notifications")
async def clear_notifications():
    """Clear all notifications (for testing purposes)"""
    notifications_db.clear()
    return {"message": "All notifications cleared"}

class ManualNotificationRequest(BaseModel):
    employee_id: str
    employee_name: str
    message: str

@app.post("/notifications/manual", response_model=Notification)
async def send_manual_notification(request: ManualNotificationRequest):
    """Send a manual notification to an employee"""
    notification = Notification(
        id=generate_id(),
        winner_id="manual",
        employee_id=request.employee_id,
        employee_name=request.employee_name,
        category="Manual Notification",
        message=request.message,
        sent=True,
        created_at=get_current_timestamp()
    )
    
    notifications_db[notification.id] = notification
    return notification

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)