# DundieAwardsBackend

Backend microservices for The Office's Dundie Awards nomination and voting system. This monorepo contains four Python microservices that work together to manage the complete awards flow: nominations → voting → winners → notifications.

## 🏆 The Dundie Awards System

*"The Dundie Award for Longest Engagement goes to... Pam and Roy!"* - Michael Scott

This system manages the most prestigious awards ceremony in Scranton, PA, featuring categories like:
- 🔥 Hottest in the Office
- 👟 Whitest Sneakers  
- 🦫 Busiest Beaver
- 🌶️ Spiciest in the Office
- 💰 Show Me The Money
- ✨ Fine Work
- 👔 Best Dressed
- 💍 Longest Engagement

## 🏗️ Architecture

The system consists of five FastAPI microservices:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nominations   │───▶│     Voting      │───▶│    Winners      │───▶│ Notifications   │
│   Service       │    │    Service      │    │   Service       │    │   Service       │
│   Port: 8001    │    │   Port: 8002    │    │   Port: 8003    │    │   Port: 8004    │
└─────┬─────▲─────┘    └─────┬─────▲─────┘    └─────┬─────▲─────┘    └─────┬─────▲─────┘
      │     │               │     │               │     │               │     │
      │     │               │     │               │     │               │     │
      │     └───────────────┴─────┴───────────────┴─────┴───────────────┴─────┘
      │
      │                    ┌──────────────────────────────────────┐
      └───────────────────▶│         Azure Service Bus            │
                           │    (via azure-servicebus SDK)        │
                           └─────────────┬───────────────┬────────┘
                                         │               │
                                         │               │
                                         │               │
                ┌────────────────────────┘               └───────────────┐
                │                                                      │
                ▼                                                      ▼
      ┌────────────────────────────┐                        ┌────────────────────────────┐
      │   Security/Audit Service     │                        │  Other Event-Driven         │
      │  "Dwight's Security Desk"  │                        │  Microservices (future)     │
      │      Port: 8005           │                        └────────────────────────────┘
      └────────────────────────────┘
```

### Services Overview

#### 1. **Nominations Service** (Port 8001)
- Manages award nominations
- Stores employee data
- Validates nomination requests
- **Endpoints**: `/nominations`, `/employees`

#### 2. **Voting Service** (Port 8002)  
- Handles voting on nominations
- Prevents duplicate voting
- Tracks vote counts per nomination
- **Endpoints**: `/votes`, `/votes/results`

#### 3. **Winners Service** (Port 8003)
- Calculates winners based on vote counts
- Determines one winner per award category
- Manages winner data
- **Endpoints**: `/winners/calculate`, `/winners`

#### 4. **Notifications Service** (Port 8004)
- Sends congratulatory messages to winners
- Tracks notification delivery
- Supports manual notifications
- **Endpoints**: `/notifications/send`, `/notifications`

#### 5. **Security/Audit Service** (Port 8005) - "Dwight's Security Desk"
- Monitors and investigates suspicious activities
- Processes audit events from all other services
- Tracks user activities and sensitive operations
- Calculates risk scores for security events
- **Endpoints**: `/audit/logs`, `/audit/suspicious`, `/audit/metrics`

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Running with Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DundieAwardsBackend
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Run the demo**
   ```bash
   python demo.py
   ```

4. **Access service APIs**
   - Nominations: http://localhost:8001/docs
   - Voting: http://localhost:8002/docs
   - Winners: http://localhost:8003/docs
   - Notifications: http://localhost:8004/docs
   - Security (Dwight's Desk): http://localhost:8005/docs
   - Notifications: http://localhost:8004/docs

### Running Locally for Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r test-requirements.txt
   ```

2. **Start services in separate terminals**
   ```bash
   # Terminal 1 - Nominations Service
   python services/nominations/main.py
   
   # Terminal 2 - Voting Service  
   python services/voting/main.py
   
   # Terminal 3 - Winners Service
   python services/winners/main.py
   
   # Terminal 4 - Notifications Service
   python services/notifications/main.py
   ```

3. **Run the demo**
   ```bash
   python demo.py
   ```

## 📋 Usage Examples

### 1. Create a Nomination
```bash
curl -X POST "http://localhost:8001/nominations" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "emp_001",
    "category": "Hottest in the Office", 
    "nominator_id": "emp_002",
    "reason": "Jim is clearly the hottest person in Scranton"
  }'
```

### 2. Cast a Vote
```bash
curl -X POST "http://localhost:8002/votes" \
  -H "Content-Type: application/json" \
  -d '{
    "nomination_id": "nomination-id-here",
    "voter_id": "emp_003"
  }'
```

### 3. Calculate Winners
```bash
curl -X POST "http://localhost:8003/winners/calculate"
```

### 4. Send Notifications
```bash
curl -X POST "http://localhost:8004/notifications/send"
```

## 🎬 Complete Demo Flow

The included `demo.py` script demonstrates the complete awards flow:

```bash
python demo.py
```

This will:
1. ✅ Check service health
2. 📝 Create sample nominations for Office employees
3. 🗳️ Simulate voting (Jim, Dwight, Pam, Michael, Kevin)
4. 🏆 Calculate winners based on vote counts  
5. 📧 Send congratulatory notifications
6. 📊 Display final results summary

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

## 📁 Project Structure

```
DundieAwardsBackend/
├── services/
│   ├── nominations/
│   │   ├── main.py
│   │   └── Dockerfile
│   ├── voting/
│   │   ├── main.py
│   │   └── Dockerfile
│   ├── winners/
│   │   ├── main.py
│   │   └── Dockerfile
│   └── notifications/
│       ├── main.py
│       └── Dockerfile
├── shared/
│   ├── models.py      # Pydantic models
│   └── utils.py       # Shared utilities
├── tests/
│   └── test_nominations.py
├── docker-compose.yml
├── demo.py
└── requirements.txt
```

## 🔧 Configuration

Services communicate via HTTP REST APIs. Environment variables:

- `NOMINATIONS_SERVICE_URL` - URL for nominations service
- `VOTING_SERVICE_URL` - URL for voting service  
- `WINNERS_SERVICE_URL` - URL for winners service

Default URLs assume Docker Compose networking.

## 🎭 Office Characters Included

The system includes these beloved Dunder Mifflin employees:

- 👨‍💼 Jim Halpert (Sales)
- 👩‍💼 Pam Beesly (Reception)
- 🥕 Dwight Schrute (Sales)
- 🎭 Michael Scott (Management)
- 😴 Stanley Hudson (Sales)
- 🧮 Kevin Malone (Accounting)
- 😤 Angela Martin (Accounting)
- 🤓 Oscar Martinez (Accounting)

## 🏪 The Dundie Awards

*"I would like to give this award to the person who I admire most... me!"* - Michael Scott

The Dundie Awards are Scranton's most prestigious recognition program, held annually at Chili's restaurant with drinks provided by Michael Scott (Regional Manager and host extraordinaire).

---

*That's what she said!* 🎉
