from datetime import datetime
import uuid

def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())

def get_current_timestamp() -> datetime:
    """Get current timestamp"""
    return datetime.utcnow()

# Sample employees data for demonstration
SAMPLE_EMPLOYEES = [
    {"id": "emp_001", "name": "Jim Halpert", "department": "Sales", "email": "jim@dundermifflin.com"},
    {"id": "emp_002", "name": "Pam Beesly", "department": "Reception", "email": "pam@dundermifflin.com"},
    {"id": "emp_003", "name": "Dwight Schrute", "department": "Sales", "email": "dwight@dundermifflin.com"},
    {"id": "emp_004", "name": "Michael Scott", "department": "Management", "email": "michael@dundermifflin.com"},
    {"id": "emp_005", "name": "Stanley Hudson", "department": "Sales", "email": "stanley@dundermifflin.com"},
    {"id": "emp_006", "name": "Kevin Malone", "department": "Accounting", "email": "kevin@dundermifflin.com"},
    {"id": "emp_007", "name": "Angela Martin", "department": "Accounting", "email": "angela@dundermifflin.com"},
    {"id": "emp_008", "name": "Oscar Martinez", "department": "Accounting", "email": "oscar@dundermifflin.com"},
]