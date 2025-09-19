#!/usr/bin/env python3
"""
Demo script showing the complete Dundie Awards flow:
nominations → voting → winners → notifications
"""

import requests
import json
import time
from typing import Dict, List

# Service URLs
SERVICES = {
    "nominations": "http://localhost:8001",
    "voting": "http://localhost:8002", 
    "winners": "http://localhost:8003",
    "notifications": "http://localhost:8004"
}

def check_services_health():
    """Check if all services are running"""
    print("🔍 Checking service health...")
    for service, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service.title()} Service: Healthy")
            else:
                print(f"❌ {service.title()} Service: Unhealthy")
                return False
        except Exception as e:
            print(f"❌ {service.title()} Service: Unreachable - {e}")
            return False
    return True

def create_sample_nominations():
    """Create sample nominations for the demo"""
    print("\n📝 Creating sample nominations...")
    
    nominations = [
        {
            "employee_id": "emp_001", 
            "category": "Hottest in the Office",
            "nominator_id": "emp_002",
            "reason": "Jim's smoldering good looks and pranking skills make hearts race"
        },
        {
            "employee_id": "emp_003",
            "category": "Busiest Beaver", 
            "nominator_id": "emp_004",
            "reason": "Dwight works tirelessly on beet farm management and bear safety protocols"
        },
        {
            "employee_id": "emp_002",
            "category": "Fine Work",
            "nominator_id": "emp_001", 
            "reason": "Pam's art and reception skills deserve recognition"
        },
        {
            "employee_id": "emp_004",
            "category": "Show Me The Money",
            "nominator_id": "emp_005",
            "reason": "Michael's leadership brings in the big sales (World's Best Boss mug says so)"
        },
        {
            "employee_id": "emp_006",
            "category": "Whitest Sneakers",
            "nominator_id": "emp_007",
            "reason": "Kevin's New Balance sneakers are pristinely white"
        }
    ]
    
    created_nominations = []
    for nom_data in nominations:
        try:
            response = requests.post(f"{SERVICES['nominations']}/nominations", json=nom_data)
            if response.status_code == 200:
                nomination = response.json()
                created_nominations.append(nomination)
                print(f"✅ Created nomination: {nomination['employee_name']} for '{nomination['category']}'")
            else:
                print(f"❌ Failed to create nomination: {response.text}")
        except Exception as e:
            print(f"❌ Error creating nomination: {e}")
    
    return created_nominations

def simulate_voting(nominations: List[Dict]):
    """Simulate voting on the nominations"""
    print("\n🗳️  Simulating voting...")
    
    # Sample voting patterns - some nominations get more votes
    voting_patterns = {
        0: ["emp_002", "emp_003", "emp_004", "emp_005"],  # Jim gets 4 votes
        1: ["emp_001", "emp_002", "emp_006"],              # Dwight gets 3 votes  
        2: ["emp_001", "emp_003", "emp_004", "emp_006", "emp_007"], # Pam gets 5 votes
        3: ["emp_001", "emp_003"],                         # Michael gets 2 votes
        4: ["emp_001", "emp_002", "emp_003", "emp_007"]    # Kevin gets 4 votes
    }
    
    for i, nomination in enumerate(nominations):
        if i in voting_patterns:
            voters = voting_patterns[i]
            print(f"\n📋 Voting for {nomination['employee_name']} ({nomination['category']}):")
            
            for voter_id in voters:
                vote_data = {
                    "nomination_id": nomination["id"],
                    "voter_id": voter_id
                }
                try:
                    response = requests.post(f"{SERVICES['voting']}/votes", json=vote_data)
                    if response.status_code == 200:
                        vote = response.json()
                        print(f"  ✅ {vote['voter_name']} voted")
                    else:
                        print(f"  ❌ Vote failed: {response.text}")
                except Exception as e:
                    print(f"  ❌ Error voting: {e}")

def calculate_winners():
    """Calculate winners based on votes"""
    print("\n🏆 Calculating winners...")
    
    try:
        response = requests.post(f"{SERVICES['winners']}/winners/calculate")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            
            for winner in result['winners']:
                print(f"🏆 {winner['employee_name']} won '{winner['category']}' with {winner['total_votes']} votes!")
            
            return result['winners']
        else:
            print(f"❌ Failed to calculate winners: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error calculating winners: {e}")
        return []

def send_notifications():
    """Send notifications to winners"""
    print("\n📧 Sending notifications to winners...")
    
    try:
        response = requests.post(f"{SERVICES['notifications']}/notifications/send")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            
            # Show sample notification
            if result['notifications']:
                sample_notification = result['notifications'][0]
                print(f"\n📨 Sample notification to {sample_notification['employee_name']}:")
                print("-" * 50)
                print(sample_notification['message'])
                print("-" * 50)
                
        else:
            print(f"❌ Failed to send notifications: {response.text}")
    except Exception as e:
        print(f"❌ Error sending notifications: {e}")

def show_final_results():
    """Display final results summary"""
    print("\n📊 Final Results Summary:")
    print("=" * 60)
    
    try:
        # Get winners
        response = requests.get(f"{SERVICES['winners']}/winners")
        if response.status_code == 200:
            winners = response.json()
            
            if not winners:
                print("No winners found!")
                return
                
            for winner in winners:
                print(f"🏆 {winner['category']}")
                print(f"   Winner: {winner['employee_name']}")
                print(f"   Votes: {winner['total_votes']}")
                print(f"   Reason: {winner['reason']}")
                print()
        else:
            print("Failed to get winners")
            
        # Get notification count
        response = requests.get(f"{SERVICES['notifications']}/notifications")
        if response.status_code == 200:
            notifications = response.json()
            print(f"📧 {len(notifications)} notifications sent")
            
    except Exception as e:
        print(f"❌ Error getting final results: {e}")

def main():
    """Run the complete Dundie Awards demo"""
    print("🏆 Welcome to the Dundie Awards Backend Demo! 🏆")
    print("=" * 60)
    
    if not check_services_health():
        print("\n❌ Some services are not running. Please start all services first.")
        print("Run: docker-compose up -d")
        return
    
    # Step 1: Create nominations
    nominations = create_sample_nominations()
    if not nominations:
        print("❌ No nominations created. Exiting.")
        return
    
    time.sleep(1)
    
    # Step 2: Simulate voting
    simulate_voting(nominations)
    
    time.sleep(1)
    
    # Step 3: Calculate winners
    winners = calculate_winners()
    
    time.sleep(1)
    
    # Step 4: Send notifications
    send_notifications()
    
    time.sleep(1)
    
    # Step 5: Show final results
    show_final_results()
    
    print("\n🎉 Dundie Awards ceremony complete!")
    print("Thanks for participating in the most prestigious award ceremony in Scranton!")

if __name__ == "__main__":
    main()