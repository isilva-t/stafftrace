# Deployment Guide - Docker, Kubernetes, Environment Configuration

## Overview

This document covers:
- Environment configuration (.env files)
- Docker containerization
- Kubernetes deployment on GKE
- Build timeline and phases
- Post-MVP: Terraform and CI/CD

---

## Environment Configuration

### Django Agent .env
```bash
# agent/.env

# Django settings
SECRET_KEY=your-django-secret-key-generate-random-string
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100

# Database (PostgreSQL)
DATABASE_NAME=presence_monitor
DATABASE_USER=postgres
DATABASE_PASSWORD=strong-password-here
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cloud API configuration
CLOUD_API_URL=https://your-backend.example.com
SITE_ID=porto_office

# Timezone
TZ=Europe/Lisbon
```

### Spring Boot Backend .env
```bash
# backend/.env

# MongoDB
MONGODB_URI=mongodb://mongodb:27017/presence_monitor
# Or MongoDB Atlas: mongodb+srv://user:pass@cluster.mongodb.net/presence_monitor

# JWT configuration
JWT_SECRET=generate-random-256-bit-secret-key-change-in-production

# Admin credentials (hardcoded for MVP)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=demo123

# Server
SERVER_PORT=8080
```

### Angular Frontend Environment
```typescript
// frontend/src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://your-backend.example.com/api'
};
```

---

## Docker Configuration

### Django Agent Dockerfile
```dockerfile
# agent/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start services
CMD python manage.py migrate && \
    python manage.py check_outage && \
    celery -A config worker -l info & \
    celery -A config beat -l info & \
    python manage.py runserver 0.0.0.0:8000
```

### Spring Boot Dockerfile
```dockerfile
# backend/Dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /app
COPY pom.xml .
COPY src ./src

RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Angular Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build --configuration=production

FROM nginx:alpine

COPY --from=build /app/dist/frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration (for Angular)
```nginx
# frontend/nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy (optional, for CORS)
        location /api {
            proxy_pass http://backend:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

---

## Docker Compose (Local Testing)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: presence_monitor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  django-agent:
    build: ./agent
    env_file:
      - ./agent/.env
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  spring-backend:
    build: ./backend
    env_file:
      - ./backend/.env
    depends_on:
      - mongodb
    ports:
      - "8080:8080"

  angular-frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - spring-backend

volumes:
  postgres_data:
  mongo_data:
```

**Run locally**:
```bash
docker-compose up --build
```

---

## Kubernetes Deployment (GKE)

### Prerequisites
```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create GKE cluster (one-time)
gcloud container clusters create presence-monitor \
  --zone=europe-west1-b \
  --num-nodes=2 \
  --machine-type=e2-medium

# Get credentials
gcloud container clusters get-credentials presence-monitor \
  --zone=europe-west1-b
```

### ConfigMap for Environment Variables
```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  MONGODB_URI: "mongodb://mongodb:27017/presence_monitor"
  SERVER_PORT: "8080"
---
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  JWT_SECRET: "your-jwt-secret-base64-encoded"
  ADMIN_USERNAME: "admin"
  ADMIN_PASSWORD: "demo123"
```

### MongoDB Deployment
```yaml
# kubernetes/mongodb-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongo-storage
          mountPath: /data/db
      volumes:
      - name: mongo-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
  type: ClusterIP
```

### Spring Boot Backend Deployment
```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: gcr.io/YOUR_PROJECT_ID/presence-backend:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### Angular Frontend Deployment
```yaml
# kubernetes/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: gcr.io/YOUR_PROJECT_ID/presence-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

### Deploy to Kubernetes
```bash
# Build and push images
docker build -t gcr.io/YOUR_PROJECT_ID/presence-backend:latest ./backend
docker build -t gcr.io/YOUR_PROJECT_ID/presence-frontend:latest ./frontend

docker push gcr.io/YOUR_PROJECT_ID/presence-backend:latest
docker push gcr.io/YOUR_PROJECT_ID/presence-frontend:latest

# Apply Kubernetes manifests
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/mongodb-deployment.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml

# Check status
kubectl get pods
kubectl get services

# Get external IPs
kubectl get service backend
kubectl get service frontend
```

---

## Build Timeline

### MVP Phase (Days 1-4)

**Day 1: Django Agent**
- Setup Django project
- Create models (Users, Devices, StateChanges, HourlySummary, SystemStatus)
- Implement ping logic
- Setup Celery tasks
- Configure Django Admin
- Test locally with PostgreSQL

**Day 2: Spring Boot Backend**
- Setup Spring Boot project
- Create MongoDB models (CurrentStatus, DailyPresence)
- Implement JWT service
- Create REST endpoints (heartbeat, presence, current, daily, monthly)
- Test with Postman

**Day 3: Angular Frontend**
- Setup Angular project
- Create services (auth, api)
- Implement 4 components (current, daily, monthly, employee detail)
- Basic styling
- Test with mock data, then connect to backend

**Day 4: Docker + Manual K8s**
- Write Dockerfiles for backend and frontend
- Test with docker-compose locally
- Create Kubernetes manifests
- Deploy to GKE manually
- Verify end-to-end functionality

**Deliverable**: Working MVP with all core features

---

### Post-MVP Phase (Days 5-7)

**Day 5: Terraform Infrastructure**
```bash
# terraform/main.tf - Example structure
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "primary" {
  name     = "presence-monitor"
  location = var.zone

  initial_node_count = 2

  node_config {
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

resource "google_compute_address" "backend_ip" {
  name = "backend-ip"
}

resource "google_compute_address" "frontend_ip" {
  name = "frontend-ip"
}
```

**Commands**:
```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

**Day 6-7: GitHub Actions CI/CD**
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup gcloud
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Configure Docker
      run: gcloud auth configure-docker
    
    - name: Build Backend
      run: |
        docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/presence-backend:${{ github.sha }} ./backend
        docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/presence-backend:${{ github.sha }}
    
    - name: Build Frontend
      run: |
        docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/presence-frontend:${{ github.sha }} ./frontend
        docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/presence-frontend:${{ github.sha }}
    
    - name: Deploy to GKE
      run: |
        gcloud container clusters get-credentials presence-monitor --zone=europe-west1-b
        kubectl set image deployment/backend backend=gcr.io/${{ secrets.GCP_PROJECT_ID }}/presence-backend:${{ github.sha }}
        kubectl set image deployment/frontend frontend=gcr.io/${{ secrets.GCP_PROJECT_ID }}/presence-frontend:${{ github.sha }}
        kubectl rollout status deployment/backend
        kubectl rollout status deployment/frontend
```

---

## Repository Structure

```
employee-presence-monitor/
├── agent/                          # Django on-premise service
│   ├── monitoring/
│   ├── config/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── backend/                        # Spring Boot cloud service
│   ├── src/
│   ├── pom.xml
│   ├── Dockerfile
│   └── .env.example
├── frontend/                       # Angular dashboard
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── kubernetes/                     # K8s manifests
│   ├── configmap.yaml
│   ├── mongodb-deployment.yaml
│   ├── backend-deployment.yaml
│   └── frontend-deployment.yaml
├── terraform/                      # Infrastructure as Code (post-MVP)
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── .github/
│   └── workflows/
│       └── deploy.yml             # CI/CD pipeline (post-MVP)
├── docker-compose.yml             # Local testing
├── README.md
└── docs/                          # This documentation
    ├── 01-system-architecture.md
    ├── 02-django-agent.md
    ├── 03-spring-boot-backend.md
    ├── 04-angular-frontend.md
    └── 05-deployment.md
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Use strong JWT secret (256-bit minimum)
- [ ] Enable HTTPS only (use cert-manager in K8s)
- [ ] Restrict CORS to specific domains
- [ ] Use secrets management (Google Secret Manager)
- [ ] Enable network policies in K8s

### Monitoring
- [ ] Setup Cloud Logging
- [ ] Setup Cloud Monitoring
- [ ] Add health check endpoints
- [ ] Configure alerts for downtime

### Performance
- [ ] Enable horizontal pod autoscaling
- [ ] Add database indexes
- [ ] Setup CDN for frontend
- [ ] Enable gzip compression

### Backup
- [ ] Schedule PostgreSQL backups (on-premise)
- [ ] Schedule MongoDB backups (Atlas or GCP)
- [ ] Test restore procedures

---

## Cost Estimation (GCP)

**Monthly costs for MVP**:
- GKE cluster (2 e2-medium nodes): ~$60-80
- Load Balancers (2): ~$36
- Cloud Logging/Monitoring: ~$10
- Container Registry: ~$5

**Total**: ~$110-130/month

**Free tier alternatives**:
- MongoDB Atlas (Free tier: 512MB)
- Django Agent runs on-premise (no cloud cost)

---

## Troubleshooting

### Common Issues

**Django agent can't connect to cloud**:
```bash
# Check network connectivity
curl https://your-backend.example.com/api/heartbeat

# Check environment variables
python manage.py shell
>>> import os
>>> os.getenv('CLOUD_API_URL')
```

**Kubernetes pod crashes**:
```bash
# Check logs
kubectl logs deployment/backend

# Describe pod
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by='.lastTimestamp'
```

**MongoDB connection issues**:
```bash
# Test connection from pod
kubectl exec -it <backend-pod> -- sh
curl mongodb:27017

# Check service
kubectl get svc mongodb
```

---

## Related Documents
- [01-system-architecture.md](./01-system-architecture.md) - System overview
- [02-django-agent.md](./02-django-agent.md) - Django implementation
- [03-spring-boot-backend.md](./03-spring-boot-backend.md) - Spring Boot implementation
- [04-angular-frontend.md](./04-angular-frontend.md) - Angular implementation

---

## Quick Start Commands

### Local Development
```bash
# Start all services
docker-compose up

# Django admin
http://localhost:8000/admin

# Backend API
http://localhost:8080/api

# Frontend
http://localhost:80
```

### Production Deployment
```bash
# Deploy to GKE
./deploy.sh

# Or manually
kubectl apply -f kubernetes/
```

### Access Application
- **Frontend**: Get LoadBalancer IP with `kubectl get svc frontend`
- **Backend API**: Get LoadBalancer IP with `kubectl get svc backend`
- **Credentials**: admin / demo123 (from .env)
