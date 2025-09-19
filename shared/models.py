from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

class AwardCategory(str, Enum):
    HOTTEST_IN_THE_OFFICE = "Hottest in the Office"
    WHITEST_SNEAKERS = "Whitest Sneakers"
    BUSIEST_BEAVER = "Busiest Beaver"
    SPICIEST_IN_THE_OFFICE = "Spiciest in the Office"
    SHOW_ME_THE_MONEY = "Show Me The Money"
    FINE_WORK = "Fine Work"
    BEST_DRESSED = "Best Dressed"
    LONGEST_ENGAGEMENT = "Longest Engagement"

class Employee(BaseModel):
    id: str
    name: str
    department: str
    email: Optional[str] = None

class Nomination(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    category: AwardCategory
    nominator_id: str
    nominator_name: str
    reason: str
    created_at: datetime

class Vote(BaseModel):
    id: str
    nomination_id: str
    voter_id: str
    voter_name: str
    created_at: datetime

class Winner(BaseModel):
    id: str
    nomination_id: str
    employee_id: str
    employee_name: str
    category: AwardCategory
    total_votes: int
    reason: str
    created_at: datetime

class Notification(BaseModel):
    id: str
    winner_id: str
    employee_id: str
    employee_name: str
    category: AwardCategory
    message: str
    sent: bool = False
    created_at: datetime