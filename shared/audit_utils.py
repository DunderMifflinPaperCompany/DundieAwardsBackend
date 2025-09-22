import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from .models import AuditEvent, AuditEventType
from .utils import generate_id, get_current_timestamp

class AuditEventPublisher:
    """Azure Service Bus publisher for audit events"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv(
            "AZURE_SERVICEBUS_CONNECTION_STRING", 
            "mock://localhost"  # Mock connection for development
        )
        self.topic_name = "audit-events"
        self._client = None
    
    async def get_client(self):
        """Get or create Service Bus client"""
        if self._client is None:
            if self.connection_string.startswith("mock://"):
                # Mock client for development/testing
                self._client = MockServiceBusClient()
            else:
                self._client = ServiceBusClient.from_connection_string(self.connection_string)
        return self._client
    
    async def publish_event(
        self,
        event_type: AuditEventType,
        service_name: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        details: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Publish an audit event to Service Bus"""
        try:
            event = AuditEvent(
                id=generate_id(),
                event_type=event_type,
                service_name=service_name,
                user_id=user_id,
                user_name=user_name,
                resource_id=resource_id,
                resource_type=resource_type,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=get_current_timestamp()
            )
            
            client = await self.get_client()
            if hasattr(client, 'get_topic_sender'):
                # Real Azure Service Bus
                sender = client.get_topic_sender(topic_name=self.topic_name)
                message = ServiceBusMessage(event.model_dump_json())
                await sender.send_messages(message)
                await sender.close()
            else:
                # Mock client - just log the event
                print(f"[AUDIT] {event.event_type}: {event.model_dump_json()}")
            
        except Exception as e:
            # Don't let audit failures break the main service
            print(f"Failed to publish audit event: {e}")
    
    async def close(self):
        """Close the Service Bus client"""
        if self._client and hasattr(self._client, 'close'):
            await self._client.close()

class MockServiceBusClient:
    """Mock Service Bus client for development/testing"""
    
    def __init__(self):
        self.messages = []
    
    async def close(self):
        pass

# Global publisher instance
_audit_publisher = None

async def get_audit_publisher() -> AuditEventPublisher:
    """Get the global audit publisher instance"""
    global _audit_publisher
    if _audit_publisher is None:
        _audit_publisher = AuditEventPublisher()
    return _audit_publisher

async def audit_nomination_submitted(nominator_id: str, nominator_name: str, employee_id: str, category: str, nomination_id: str):
    """Audit event for nomination submission"""
    publisher = await get_audit_publisher()
    await publisher.publish_event(
        event_type=AuditEventType.NOMINATION_SUBMITTED,
        service_name="nominations",
        user_id=nominator_id,
        user_name=nominator_name,
        resource_id=nomination_id,
        resource_type="nomination",
        details={
            "employee_id": employee_id,
            "category": category,
            "action": "nomination_created"
        }
    )

async def audit_vote_cast(voter_id: str, voter_name: str, nomination_id: str, vote_id: str):
    """Audit event for vote casting"""
    publisher = await get_audit_publisher()
    await publisher.publish_event(
        event_type=AuditEventType.VOTE_CAST,
        service_name="voting",
        user_id=voter_id,
        user_name=voter_name,
        resource_id=vote_id,
        resource_type="vote",
        details={
            "nomination_id": nomination_id,
            "action": "vote_created"
        }
    )

async def audit_winner_calculated(category: str, winner_id: str, total_votes: int):
    """Audit event for winner calculation"""
    publisher = await get_audit_publisher()
    await publisher.publish_event(
        event_type=AuditEventType.WINNER_CALCULATED,
        service_name="winners",
        resource_id=winner_id,
        resource_type="winner",
        details={
            "category": category,
            "total_votes": total_votes,
            "action": "winner_calculated"
        }
    )

async def audit_notification_sent(winner_id: str, employee_id: str, employee_name: str, notification_id: str):
    """Audit event for notification sending"""
    publisher = await get_audit_publisher()
    await publisher.publish_event(
        event_type=AuditEventType.NOTIFICATION_SENT,
        service_name="notifications",
        user_id=employee_id,
        user_name=employee_name,
        resource_id=notification_id,
        resource_type="notification",
        details={
            "winner_id": winner_id,
            "action": "notification_sent"
        }
    )

def calculate_risk_score(event: AuditEvent) -> int:
    """Calculate risk score for an audit event (0-100)"""
    score = 0
    
    # Base risk scores by event type
    risk_scores = {
        AuditEventType.NOMINATION_SUBMITTED: 10,
        AuditEventType.VOTE_CAST: 15,
        AuditEventType.WINNER_CALCULATED: 20,
        AuditEventType.NOTIFICATION_SENT: 5,
        AuditEventType.SUSPICIOUS_ACTIVITY: 80
    }
    
    score += risk_scores.get(event.event_type, 0)
    
    # Increase risk for missing user information
    if not event.user_id:
        score += 20
    
    # Increase risk for certain patterns in details
    if event.details:
        if "multiple" in str(event.details).lower():
            score += 15
        if "rapid" in str(event.details).lower():
            score += 25
    
    return min(score, 100)