# Employee Presence Monitoring Platform - System Architecture

## Project Overview

**Purpose**: Track employee attendance and working hours in small office environments by monitoring device presence on local network via IP ping checks.

**Scale**: 
- 6-10 devices per location
- Single office (porto_office)
- Change-based data storage (not every ping)
- Simple presence reporting (current status, daily, monthly views)

**Constraint**: Buildable in 3-4 days for technical interview demonstration.

---

## Architecture Pattern

### Two-Service Microservices Design

**Service 1: On-Premise Monitoring Agent (Django)**
- Runs locally on office network
- Pings configured IP addresses periodically
- Stores state changes in PostgreSQL
- Pushes heartbeats and hourly summaries to cloud
- Provides Django Admin interface for device management

**Service 2: Cloud Dashboard (Spring Boot + Angular)**
- Receives data from on-premise agent
- Stores aggregated data in MongoDB
- Provides web dashboard for presence reporting
- Handles JWT authentication and name anonymization

---

## Communication Pattern

### Push Model (Local → Cloud)

**Security Benefits**:
- Outbound HTTPS only
- No inbound traffic to local network
- Zero-trust principles
- Local network remains isolated

**Two Data Flows**:

1. **Heartbeat** (every 5 minutes)
   - Lightweight: Just list of currently online devices
   - Updates CurrentStatus in cloud
   - Enables real-time "who's here now?" view

2. **Hourly Summary** (every 60 minutes)
   - Detailed: first_seen, last_seen, minutes_online
   - Updates DailyPresence in cloud
   - Enables historical reporting

---

## Technology Stack

### On-Premise Agent
- **Language**: Python 3.11+
- **Framework**: Django 5.0
- **Database**: PostgreSQL 15
- **Task Scheduler**: Celery + Redis (or Django-Q)
- **Admin Interface**: Django Admin (built-in)

**Why These Choices**:
- Django keyword for ATS
- Built-in admin panel (free local UI)
- PostgreSQL for reliable historical data
- Python for rapid development

### Cloud Backend
- **Language**: Java 17+
- **Framework**: Spring Boot 3.2
- **Database**: MongoDB 7
- **Authentication**: JWT (io.jsonwebtoken)
- **API**: RESTful endpoints

**Why These Choices**:
- Java/Spring Boot: Enterprise standard
- MongoDB: Flexible schema, NoSQL keyword
- Demonstrates polyglot persistence

### Cloud Frontend
- **Framework**: Angular 17
- **Styling**: Plain CSS (no frameworks)
- **HTTP Client**: Angular HttpClient
- **Auth Storage**: localStorage

**Why These Choices**:
- Angular: Enterprise frontend standard
- Simple UI: Focus on functionality

### Infrastructure
- **Cloud Platform**: Google Cloud Platform (GCP)
- **Orchestration**: Kubernetes (GKE)
- **Containerization**: Docker
- **IaC**: Terraform (post-MVP)
- **CI/CD**: GitHub Actions (post-MVP)

---

## Data Flow

### 1. Device Detection (Every 60 seconds)
```
Django Agent → Ping IP addresses
             → Check response
             → Detect state change (online↔offline)
             → Store in StateChanges table (if changed)
             → Update in-memory failure tracker
```

### 2. Heartbeat (Every 5 minutes)
```
Django Agent → Query current online devices
             → POST /api/heartbeat
             → {devices_online: [user_ids]}

Spring Boot  → Update CurrentStatus collection
             → Mark online devices as present
             → Mark devices not in list as absent (if >10min)
```

### 3. Hourly Summary (Every 60 minutes)
```
Django Agent → Calculate from StateChanges
             → first_seen, last_seen, minutes_online
             → POST /api/presence
             → {employee data for past hour}

Spring Boot  → Upsert DailyPresence collection
             → Aggregate daily totals
```

### 4. Frontend Display
```
Angular      → GET /api/current (with/without JWT)
             → Spring Boot checks authentication
             → Returns real names (authenticated)
             → Returns fake names (public/demo mode)

Angular      → Render 4 views
             → Current Status, Daily, Monthly, Employee Detail
```

---

## Key Design Decisions

### State-Based Storage (Not Ping-Based)
**Decision**: Only store state changes, not every ping result

**Rationale**:
- Device online for 8 hours = 2 records (went_online, went_offline)
- vs 480 records (one per minute)
- 240x reduction in storage
- Simpler queries for "is employee present?"

**Trade-off**: Can't reconstruct exact minute-by-minute timeline, but hourly summaries are sufficient.

### Offline Threshold
**Decision**: Mark device offline after 60 seconds of failed pings

**Rationale**:
- Network glitches don't immediately mark employee absent
- Balance between accuracy and responsiveness
- Configurable constant

### In-Memory Failure Tracking
**Decision**: Track "first failed ping time" in Python dict, not database

**Rationale**:
- Avoid database writes for transient failures
- Lost on restart, but power outage detection handles that
- Simpler code

### Django Admin for Device Management
**Decision**: Use Django Admin panel instead of .env files

**Rationale**:
- Non-technical users can manage devices
- Users table supports multiple devices per employee (future)
- GUI for CRUD operations
- Professional appearance

### JWT Authentication
**Decision**: Implement JWT, not session-based auth

**Rationale**:
- Stateless (no server-side sessions)
- Works with Angular SPA
- Industry standard
- 24-hour token validity

### Name Anonymization in Backend
**Decision**: Django stores both real and fake names, Spring Boot passes through

**Rationale**:
- Centralized data (one source of truth)
- Frontend doesn't know if names are real or fake
- Easy to demo: public mode shows fake names, login shows real names

### No Weekly View
**Decision**: Only Current, Daily, Monthly, and Employee Detail views

**Rationale**:
- Weekly is trivial to add later
- Monthly + Daily covers 80% of use cases
- Reduces MVP scope

---

## Scalability Considerations

### Current Scale
- 6-10 employees
- 1 device per employee (MVP)
- ~8,640 state changes per month (worst case)
- ~1,440 heartbeats per day
- ~24 hourly summaries per day

### Future Expansion Paths
- **Multiple devices per employee**: Already supported in schema (one-to-many)
- **Multiple areas**: Add area detection from WiFi AP APIs
- **More employees**: Linear scaling, no architectural changes needed
- **Multiple sites**: Would require adding site_id back (removed for MVP)

### Performance Bottlenecks (At Scale)
- Django ping loop: Could parallelize with threading/asyncio
- MongoDB queries: Add indexes on employee_id, date fields
- Frontend: Pagination if >50 employees

---

## Security Model

### On-Premise Network
- Django agent has no inbound ports
- Only outbound HTTPS to cloud API
- PostgreSQL not exposed outside localhost
- Django Admin only accessible on local network

### Cloud API
- HTTPS only
- JWT authentication for real data
- Public endpoints return anonymized data
- No PII stored without encryption (future)

### Authentication Flow
1. User enters credentials (admin/demo123 from .env)
2. Spring Boot validates against environment variables
3. Generates JWT token (24h expiration)
4. Angular stores token in localStorage
5. All subsequent requests include token in Authorization header
6. Spring Boot validates token, returns real/fake names accordingly

---

## Working Schedule Configuration

**Hardcoded Business Rules**:
- Monday-Friday: 08:30-12:30, 14:00-18:30
- Saturday: 08:30-12:30
- Sunday: Closed

**Full Day Definition**: 8+ hours on site
**Partial Day**: Less than 8 hours, but present
**Absent**: 0 hours on site

---

## Business Value

### For Employers
- Non-invasive attendance tracking
- No additional hardware (uses existing devices)
- Local data retention for compliance
- Cloud aggregation for reporting
- Identifies attendance patterns

### For Employees
- Transparent tracking (they know their device is monitored)
- Historical record access
- No biometric data collection

### For Portfolio
- **Keywords**: Microservices, Spring Boot, Angular, Django, PostgreSQL, MongoDB, Kubernetes, GCP, Docker, REST API, JWT
- **Skills**: Full-stack, cloud architecture, database design, authentication
- **Scale**: Realistic (not over-engineered toy project)
- **Timeline**: Achievable in 3-4 days

---

## Interview Talking Points

### Architecture
"I chose a microservices architecture with push-based communication for security - the on-premise agent only makes outbound HTTPS calls, no inbound traffic to the local network. This follows zero-trust principles."

### Technology Choices
"Spring Boot and Angular are enterprise standards in Portuguese companies. I added Django for on-premise collection because it provides a built-in admin interface, saving development time on local management UI."

### Database Design
"PostgreSQL stores complete historical state changes locally for data independence and compliance. MongoDB in the cloud aggregates data across time periods with a flexible schema. This demonstrates polyglot persistence."

### Scalability
"Current scale is 6-10 employees, but the architecture supports expansion. The schema already handles multiple devices per employee, and adding area tracking just requires WiFi AP integration - no architectural changes."

### MVP Scope
"I focused on core functionality for a 3-4 day build window. Features like Terraform and CI/CD are post-MVP additions. The system is fully functional for demonstrating microservices, cloud deployment, and full-stack development."

---

## Related Documents
- [02-django-agent.md](./02-django-agent.md) - On-premise service implementation
- [03-spring-boot-backend.md](./03-spring-boot-backend.md) - Cloud backend implementation
- [04-angular-frontend.md](./04-angular-frontend.md) - Frontend implementation
- [05-deployment.md](./05-deployment.md) - Deployment and configuration
