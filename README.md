# StaffTrace

`Java` `Spring Boot` `Angular` `Django` `Python` `PostgreSQL` `MongoDB` `Docker` `Kubernetes` `GCP` `Terraform` `CI/CD`

**Live Demo:** https://stafftrace.xyz

---

## What It Does

Employee presence monitoring system that tracks attendance via network connection state.

**Origin:** Needed a time clock. Had a dedicated Linux server and smartphones on WiFi. Built a solution with what was available.

Demonstrates microservices architecture and cloud deployment in production, focusing on reliability, scalability, and real-world DevOps patterns.

![Main Dashboard](assets/dashboard.png)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ON-PREMISE NETWORK                        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Django Agent                           │  │
│  │  • Monitors device presence (network ping)                │  │
│  │  • Tracks multiple devices per employee                   │  │
│  │  • Stores locally in PostgreSQL                           │  │
│  │  • Celery periodic tasks                                  │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                           │
│                      │ HTTPS (Push Model)                        │
│                      │ • Heartbeats (5 min)                      │
│                      │ • Hourly summaries                        │
└──────────────────────┼───────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │    GOOGLE CLOUD PLATFORM     │
         │                              │
         │  ┌────────────────────────┐ │
         │  │  Spring Boot Backend   │ │
         │  │  • REST API            │ │
         │  │  • JWT Authentication  │ │
         │  │  • MongoDB Atlas       │ │
         │  └──────────┬─────────────┘ │
         │             │                │
         │             │ HTTP/JSON      │
         │             ▼                │
         │  ┌────────────────────────┐ │
         │  │  Angular Frontend      │ │
         │  │  • Real-time dashboard │ │
         │  │  • Reports & analytics │ │
         │  │  • Nginx web server    │ │
         │  └────────────────────────┘ │
         │                              │
         └──────────────────────────────┘
                       │
                       │ HTTPS
                       ▼
                   End Users
```

### Three-Component Microservices Design

**On-Premise Agent (Django)**
- Monitors device presence via network pings
- Handles multiple devices per employee (smartphones with 2.4GHz and 5GHz WiFi)
- Logic: One device online = employee present; All devices offline = employee absent
- Stores complete state history locally in PostgreSQL
- Pushes heartbeats and summaries to cloud via HTTPS

**Cloud Backend (Spring Boot)**
- Receives agent data through REST endpoints
- Aggregates presence records in MongoDB Atlas
- Provides authenticated API with JWT
- Returns real or anonymized employee names based on auth

**Cloud Frontend (Angular)**
- Real-time status dashboard
- Daily and monthly presence reports
- Agent health monitoring with visual indicators
- Responsive design with mobile support

### Push-Based Communication Model

Agent initiates all communication (outbound HTTPS only):
- **Heartbeat** (every 5 minutes): List of currently online devices
- **Hourly Summary**: Detailed presence data with first_seen, last_seen, minutes_online

**Security Benefits:** 
- No inbound traffic to local network
- Zero-trust principles
- Local network remains isolated
- Agent operates independently even during cloud outages

---

## Tech Stack

### On-Premise Agent
| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| Framework | Django 5.0 |
| Database | PostgreSQL 15 |
| Task Scheduler | Celery + Redis |
| Admin Interface | Django Admin |

### Cloud Services
| Component | Technology |
|-----------|-----------|
| Backend Language | Java 17 |
| Backend Framework | Spring Boot 3.2 |
| Database | MongoDB Atlas |
| Frontend | Angular 21 |
| Authentication | JWT |
| Web Server | Nginx |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Cloud Platform | Google Cloud Platform |
| Orchestration | Kubernetes (GKE) |
| Containerization | Docker |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| DNS/SSL | Cloudflare |

---

## Key Features

- **Real-time Monitoring**: Live view of who's present on-site
- **Multiple Device Support**: Tracks 2.4GHz and 5GHz WiFi connections per employee
- **Historical Reports**: Daily and monthly presence summaries with working hours
- **JWT Authentication**: Toggle between anonymized demo mode and real employee data
- **Agent Health Tracking**: Visual indicators (HEALTHY/DEGRADED/OFFLINE/UNKNOWN)
- **Downtime Transparency**: Agent outage periods tracked and displayed with warning banners
- **Multi-Site Ready**: Architecture supports multiple office locations via siteId
- **Reliable Sync**: Database outbox pattern ensures no data loss during network issues

![Agent Log Overview](assets/agent.png)

---

## Design Decisions

### Why Microservices Push Model?
Keeps local data repository reliable even when agent is offline. On-premise data remains intact during network outages. Agent can continue monitoring and storing data locally, syncing when connectivity returns.

### Why Polyglot Persistence?
Learning new technologies through problem-solving. PostgreSQL for structured on-premise data with strong consistency. MongoDB for flexible cloud aggregation with dynamic schema evolution.

### Why Outbox Pattern?
Ensures data is never lost even if cloud API is temporarily unreachable. Failed sync attempts are retried automatically with exponential backoff. Database transactions guarantee data integrity.

### Why Multi-Site from Day 1?
Microservices architecture allows scalability from the start. Adding new offices requires no refactoring—just deploy another agent with different siteId. Backend and frontend already handle arrays of sites.

### Why Conservative Offline Marking During Agent Downtime?
Agent shows downtime information transparently with warning banners. Employees aren't incorrectly marked absent during known outages. System tracks agent health separately from employee presence.

### Why Strict Agent Health Monitoring?
Curiosity about network design patterns. Implements health thresholds based on last heartbeat timing with visual status indicators. Provides operational visibility into system reliability.

---

## Production Deployment

**Infrastructure:**
- Google Kubernetes Engine (2-node cluster, europe-west1-b)
- MongoDB Atlas (managed database service, free tier)
- Cloudflare (DNS management, SSL/TLS termination, CDN)
- Google Container Registry (Docker image storage)

**Automation:**
- GitHub Actions for CI/CD pipeline
- Automated builds and deployments on every push to main branch
- Kubernetes rolling updates for zero-downtime deployments
- Terraform for Infrastructure as Code

**Configuration:**
- Environment-based secrets management
- Kubernetes ConfigMaps and Secrets
- Shared secret token authentication between agent and backend
- HTTPS enabled across all services

**URL:** https://stafftrace.xyz

---

## Scalability Considerations

**Current Scale:**
- 6-10 employees per site
- Multiple devices per employee (already implemented)
- Single office deployment (Porto)

**Architecture Supports:**
- Multiple devices per employee: ✅ Implemented
  - Handles 2.4GHz and 5GHz WiFi cards on same smartphone
  - Logic: ANY device online = employee present
- Area-based tracking via WiFi access point integration: Planned
- Multi-site deployments: ✅ Ready (siteId field implemented)
- Horizontal scaling via Kubernetes: ✅ Configured

**Performance Optimizations:**
- State-based storage (not ping-based): 240x reduction in data volume
- Only state changes are recorded (online→offline transitions)
- Indexed MongoDB queries for fast aggregation
- Agent data retained locally for compliance and independence
- Outbox pattern with retry queue for reliable cloud sync

---

## Repository Structure

```
stafftrace/
├── agent/                      # Django on-premise service
│   ├── monitoring/
│   │   ├── models.py          # Device, StateChange, HourlySummary, AgentDowntime
│   │   ├── tasks.py           # Celery periodic tasks (ping, sync)
│   │   └── views.py           # Health endpoints
│   ├── config/
│   │   ├── settings.py
│   │   └── celery.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── backend/                    # Spring Boot cloud service  
│   ├── src/
│   │   └── main/
│   │       ├── java/
│   │       │   └── com/stafftrace/
│   │       │       ├── controller/  # REST endpoints
│   │       │       ├── service/     # Business logic
│   │       │       ├── model/       # MongoDB documents
│   │       │       └── security/    # JWT configuration
│   │       └── resources/
│   │           └── application.properties
│   ├── pom.xml
│   ├── Dockerfile
│   └── .env.example
├── frontend/                   # Angular dashboard
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/      # UI components
│   │   │   ├── services/        # HTTP services
│   │   │   └── models/          # TypeScript interfaces
│   │   └── environments/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── kubernetes/                 # K8s manifests
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── backend-deployment.yaml
│   └── frontend-deployment.yaml
├── terraform/                  # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── README.md
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD pipeline
├── docker-compose.yml         # Local development
└── README.md
```

---

## License

MIT License

Copyright (c) 2024 Ivan Teixeira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
