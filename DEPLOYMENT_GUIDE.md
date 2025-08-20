# 🚀 Deployment Guide - Data Quality Platform

## 📋 Overview

This guide covers deploying the Agentic AI Data Quality Platform in various environments, from development to production.

---

## 🏗️ Architecture Options

### 1. **Single Server Deployment**
- Frontend and Backend on same server
- SQLite database
- Local file storage
- Good for: Development, small teams, proof of concept

### 2. **Microservices Deployment**
- Separate frontend and backend services
- External database (PostgreSQL/MySQL)
- Cloud storage (AWS S3, Azure Blob)
- Good for: Production, scalability, high availability

### 3. **Containerized Deployment**
- Docker containers
- Kubernetes orchestration
- Auto-scaling capabilities
- Good for: Cloud deployment, DevOps workflows

---

## 🐳 Docker Deployment

### Quick Start with Docker Compose

1. **Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/data_quality_platform.db
      - UPLOADS_DIRECTORY=/app/data/uploads
      - OUTPUT_DIRECTORY=/app/data/outputs
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - database

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  database:
    image: postgres:15
    environment:
      - POSTGRES_DB=data_quality
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

2. **Backend Dockerfile:**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/data/outputs /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

3. **Frontend Dockerfile:**
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

4. **Deploy:**
```bash
# Clone repository
git clone <repository-url>
cd data-quality-platform

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### 1. **EC2 Instance Setup**
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Instance type: t3.medium or larger
# Security groups: Allow ports 22, 80, 443, 3000, 8000

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu

# Install application
git clone <repository-url>
cd data-quality-platform
```

#### 2. **Load Balancer Setup (ALB)**
```yaml
# alb-config.yml
apiVersion: v1
kind: Service
metadata:
  name: data-quality-platform
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 3000
      name: frontend
    - port: 8000
      targetPort: 8000
      name: backend
  selector:
    app: data-quality-platform
```

#### 3. **RDS Database Setup**
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier data-quality-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --allocated-storage 20 \
    --master-username admin \
    --master-user-password SecurePassword123 \
    --vpc-security-group-ids sg-12345678

# Update environment variables
DATABASE_URL=postgresql://admin:SecurePassword123@data-quality-db.cluster-xxx.region.rds.amazonaws.com:5432/postgres
```

#### 4. **S3 Storage Setup**
```bash
# Create S3 buckets
aws s3 mb s3://your-app-uploads
aws s3 mb s3://your-app-outputs

# Update environment variables
UPLOADS_DIRECTORY=s3://your-app-uploads
OUTPUT_DIRECTORY=s3://your-app-outputs
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Azure Deployment

#### 1. **Container Instance Setup**
```yaml
# azure-container-instance.yml
apiVersion: '2019-12-01'
location: eastus
name: data-quality-platform
properties:
  containers:
  - name: backend
    properties:
      image: your-registry/data-quality-backend:latest
      ports:
      - port: 8000
      environmentVariables:
      - name: 'AZURE_OPENAI_API_KEY'
        value: 'your-api-key'
      - name: 'DATABASE_URL'
        value: 'postgresql://user:pass@host:5432/db'
      resources:
        requests:
          cpu: 2
          memoryInGb: 4
  - name: frontend
    properties:
      image: your-registry/data-quality-frontend:latest
      ports:
      - port: 3000
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 3000
    - protocol: tcp
      port: 8000
```

#### 2. **Deploy to Azure**
```bash
# Login to Azure
az login

# Create resource group
az group create --name data-quality-rg --location eastus

# Create container instance
az container create --resource-group data-quality-rg \
  --file azure-container-instance.yml

# Get public IP
az container show --resource-group data-quality-rg \
  --name data-quality-platform --query ipAddress.ip
```

### Google Cloud Platform

#### 1. **Cloud Run Deployment**
```yaml
# cloudbuild.yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/data-quality-backend', './backend']
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/data-quality-frontend', './frontend']
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/data-quality-backend']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/data-quality-frontend']

images:
  - 'gcr.io/$PROJECT_ID/data-quality-backend'
  - 'gcr.io/$PROJECT_ID/data-quality-frontend'
```

```bash
# Deploy to Cloud Run
gcloud run deploy data-quality-backend \
  --image gcr.io/$PROJECT_ID/data-quality-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy data-quality-frontend \
  --image gcr.io/$PROJECT_ID/data-quality-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 🎛️ Kubernetes Deployment

### 1. **Namespace and ConfigMap**
```yaml
# namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: data-quality

---
# configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: data-quality
data:
  DATABASE_URL: "postgresql://user:pass@postgres-service:5432/data_quality"
  UPLOADS_DIRECTORY: "/app/data/uploads"
  OUTPUT_DIRECTORY: "/app/data/outputs"
  MAX_CONCURRENT_JOBS: "5"
```

### 2. **Secrets**
```yaml
# secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: data-quality
type: Opaque
data:
  azure-openai-api-key: <base64-encoded-api-key>
  database-password: <base64-encoded-password>
```

### 3. **Database Deployment**
```yaml
# postgres.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: data-quality
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: data_quality
        - name: POSTGRES_USER
          value: admin
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: data-quality
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: data-quality
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 4. **Backend Deployment**
```yaml
# backend.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: data-quality
spec:
  replicas: 3
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
        image: your-registry/data-quality-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: azure-openai-api-key
        envFrom:
        - configMapRef:
            name: app-config
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: data-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: data-quality
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### 5. **Frontend Deployment**
```yaml
# frontend.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: data-quality
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
        image: your-registry/data-quality-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "http://backend-service:8000"
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: data-quality
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
```

### 6. **Ingress Configuration**
```yaml
# ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: data-quality-ingress
  namespace: data-quality
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: tls-secret
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

### 7. **Deploy to Kubernetes**
```bash
# Apply configurations
kubectl apply -f namespace.yml
kubectl apply -f configmap.yml
kubectl apply -f secrets.yml
kubectl apply -f postgres.yml
kubectl apply -f backend.yml
kubectl apply -f frontend.yml
kubectl apply -f ingress.yml

# Check deployment status
kubectl get pods -n data-quality
kubectl get services -n data-quality

# Get external IP
kubectl get ingress -n data-quality
```

---

## 🔧 Production Configuration

### 1. **Environment Variables**
```env
# Production .env
NODE_ENV=production
PYTHONPATH=/app

# Database
DATABASE_URL=postgresql://user:secure_password@db-host:5432/data_quality
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-production-api-key
AZURE_OPENAI_ENDPOINT=https://your-prod-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-production
AZURE_OPENAI_API_VERSION=2024-02-01

# File Storage
UPLOADS_DIRECTORY=s3://prod-uploads-bucket
OUTPUT_DIRECTORY=s3://prod-outputs-bucket
REFERENCE_FILES_DIRECTORY=s3://prod-reference-bucket

# Performance
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT_MINUTES=60
WORKER_PROCESSES=4
MAX_FILE_SIZE_MB=500

# Security
SECRET_KEY=your-super-secure-secret-key
CORS_ORIGINS=["https://your-domain.com"]
RATE_LIMIT_PER_MINUTE=100

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_METRICS_ENABLED=true

# Redis (for caching/sessions)
REDIS_URL=redis://redis-cluster:6379/0
```

### 2. **Nginx Configuration**
```nginx
# /etc/nginx/sites-available/data-quality-platform
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # File upload limits
        client_max_body_size 500M;
        proxy_request_buffering off;
    }

    # File uploads
    location /upload {
        proxy_pass http://127.0.0.1:8000/upload;
        client_max_body_size 500M;
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 3. **SSL Certificate Setup**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 Monitoring & Logging

### 1. **Prometheus Monitoring**
```yaml
# prometheus-config.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'data-quality-backend'
    static_configs:
      - targets: ['backend-service:8000']
    metrics_path: '/metrics'

  - job_name: 'data-quality-frontend'
    static_configs:
      - targets: ['frontend-service:3000']
    metrics_path: '/api/metrics'
```

### 2. **Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "Data Quality Platform",
    "panels": [
      {
        "title": "Active Jobs",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(data_quality_active_jobs)",
            "refId": "A"
          }
        ]
      },
      {
        "title": "Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(data_quality_processing_duration_seconds_bucket[5m]))",
            "refId": "A"
          }
        ]
      }
    ]
  }
}
```

### 3. **Centralized Logging**
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log
  fields:
    service: data-quality-platform
  fields_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "data-quality-%{+yyyy.MM.dd}"

setup.template.name: "data-quality"
setup.template.pattern: "data-quality-*"
```

---

## 🔄 CI/CD Pipeline

### 1. **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker build -t ${{ secrets.REGISTRY_URL }}/data-quality-backend:${{ github.sha }} ./backend
          docker build -t ${{ secrets.REGISTRY_URL }}/data-quality-frontend:${{ github.sha }} ./frontend
      
      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login ${{ secrets.REGISTRY_URL }} -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
          docker push ${{ secrets.REGISTRY_URL }}/data-quality-backend:${{ github.sha }}
          docker push ${{ secrets.REGISTRY_URL }}/data-quality-frontend:${{ github.sha }}
      
      - name: Deploy to Kubernetes
        run: |
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
          kubectl set image deployment/backend backend=${{ secrets.REGISTRY_URL }}/data-quality-backend:${{ github.sha }} -n data-quality
          kubectl set image deployment/frontend frontend=${{ secrets.REGISTRY_URL }}/data-quality-frontend:${{ github.sha }} -n data-quality
          kubectl rollout status deployment/backend -n data-quality
          kubectl rollout status deployment/frontend -n data-quality
```

### 2. **GitLab CI/CD**
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

test:
  stage: test
  image: python:3.11
  script:
    - cd backend
    - pip install -r requirements.txt pytest
    - pytest tests/

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA ./backend
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/backend backend=$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA -n data-quality
    - kubectl set image deployment/frontend frontend=$CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA -n data-quality
  only:
    - main
```

---

## 🚀 Performance Optimization

### 1. **Database Optimization**
```sql
-- Add indexes for better query performance
CREATE INDEX idx_job_record_status ON job_record(status);
CREATE INDEX idx_job_record_created_at ON job_record(created_at);
CREATE INDEX idx_file_processing_metrics_job_id ON file_processing_metrics(job_id);

-- Partition large tables
CREATE TABLE job_record_2025 PARTITION OF job_record
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### 2. **Caching Configuration**
```python
# Redis caching
REDIS_CONFIG = {
    'host': 'redis-cluster',
    'port': 6379,
    'db': 0,
    'decode_responses': True,
    'health_check_interval': 30,
    'socket_keepalive': True,
    'socket_keepalive_options': {},
    'connection_pool_class': 'redis.BlockingConnectionPool',
    'connection_pool_class_kwargs': {
        'max_connections': 50,
        'retry_on_timeout': True,
    }
}

# Cache job results for 1 hour
CACHE_TTL_SECONDS = 3600
```

### 3. **Load Balancing**
```yaml
# HAProxy configuration
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend data_quality_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/your-domain.pem
    redirect scheme https if !{ ssl_fc }
    default_backend data_quality_backend

backend data_quality_backend
    balance roundrobin
    option httpchk GET /health
    server backend1 backend-1:8000 check
    server backend2 backend-2:8000 check
    server backend3 backend-3:8000 check
```

---

## 🔒 Security Best Practices

### 1. **Application Security**
```python
# Backend security headers
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 2. **Network Security**
```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: data-quality-network-policy
  namespace: data-quality
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### 3. **Secret Management**
```bash
# Using HashiCorp Vault
vault kv put secret/data-quality \
  azure_openai_api_key="your-api-key" \
  database_password="secure-password"

# Kubernetes secret from Vault
vault kv get -format=json secret/data-quality | \
  jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' | \
  kubectl create secret generic app-secrets --from-env-file=/dev/stdin -n data-quality
```

---

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database migrations completed
- [ ] CI/CD pipeline tested
- [ ] Security scan passed
- [ ] Performance testing completed
- [ ] Backup strategy implemented

### Deployment
- [ ] Blue-green deployment strategy
- [ ] Health checks configured
- [ ] Monitoring alerts set up
- [ ] Log aggregation working
- [ ] Auto-scaling policies defined
- [ ] Disaster recovery plan tested

### Post-deployment
- [ ] Application functionality verified
- [ ] Performance metrics baseline established
- [ ] Security monitoring active
- [ ] Backup verification completed
- [ ] Documentation updated
- [ ] Team training completed

---

*Deployment Guide v1.0.0 | Last Updated: August 20, 2025*
