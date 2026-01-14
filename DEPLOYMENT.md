# Deployment Guide

This guide provides step-by-step instructions for deploying LLM Infrastructure to various environments.

## Prerequisites

- Docker & Docker Compose (for containerized deployment)
- Node.js 18+ (for frontend development)
- Python 3.8+ (for backend services)
- Git (for version control)

---

## Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/llm-infrastructure.git
cd llm-infrastructure
```

### 2. Install Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 3. Set Up Environment Variables

**Frontend:**
```bash
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your API endpoints
```

**Backend:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run Services

**Option A: Separate Terminals**
```bash
# Terminal 1: Compliance API
cd src
python compliance_api.py

# Terminal 2: Drift API
cd src
python drift_api.py

# Terminal 3: Frontend
cd frontend
npm run dev
```

**Option B: Using Docker Compose**
```bash
docker compose up
```

Access the dashboard at `http://localhost:3000`

---

## Docker Deployment

### Building Docker Images

```bash
# Build all images
docker compose build

# Or build individual services
docker build -t llm-compliance-api -f Dockerfile .
docker build -t llm-drift-api .
docker build -t llm-dashboard ./frontend
```

### Running with Docker Compose

**Development:**
```bash
docker compose up
```

**Production:**
```bash
docker compose -f docker-compose.yml up -d
```

### Environment Configuration

Create a `docker-compose.override.yml` for production secrets:

```yaml
version: '3.8'

services:
  compliance-api:
    environment:
      - COMPLIANCE_API_HOST=0.0.0.0
      - REQUIRE_AUTHORIZATION=true
      - COMPLIANCE_API_KEY_HASH=${COMPLIANCE_API_KEY_HASH}

  drift-api:
    environment:
      - DRIFT_API_HOST=0.0.0.0

  dashboard:
    environment:
      - NEXT_PUBLIC_COMPLIANCE_API_URL=${API_URL}:5000
      - NEXT_PUBLIC_DRIFT_API_URL=${API_URL}:5001
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Docker registry access

### Deployment Steps

```bash
# Create namespace
kubectl create namespace llm-infrastructure

# Apply deployment manifests
kubectl apply -f k8s/ -n llm-infrastructure

# Check status
kubectl get pods -n llm-infrastructure

# View logs
kubectl logs -f deployment/compliance-api -n llm-infrastructure
```

### Example Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-ingress
  namespace: llm-infrastructure
spec:
  ingressClassName: nginx
  rules:
  - host: llm.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dashboard
            port:
              number: 3000
  - host: api.yourdomain.com
    http:
      paths:
      - path: /api/compliance
        pathType: Prefix
        backend:
          service:
            name: compliance-api
            port:
              number: 5000
      - path: /api/drift
        pathType: Prefix
        backend:
          service:
            name: drift-api
            port:
              number: 5001
```

---

## AWS Deployment (ECS + ALB)

### 1. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name llm-infrastructure
```

### 2. Push Images to ECR

```bash
aws ecr create-repository --repository-name llm-infrastructure

# Build and push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker build -t llm-infrastructure .
docker tag llm-infrastructure:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-infrastructure:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-infrastructure:latest
```

### 3. Create ECS Task Definition

```bash
aws ecs register-task-definition \
  --family llm-infrastructure \
  --requires-compatibilities FARGATE \
  --network-mode awsvpc \
  --cpu 512 \
  --memory 1024 \
  --container-definitions file://task-definition.json
```

### 4. Create ECS Service

```bash
aws ecs create-service \
  --cluster llm-infrastructure \
  --service-name llm-service \
  --task-definition llm-infrastructure \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

---

## GCP Deployment (Cloud Run + Cloud SQL)

### 1. Create Cloud SQL Instance

```bash
gcloud sql instances create llm-infrastructure \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

### 2. Deploy to Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/llm-infrastructure

# Deploy to Cloud Run
gcloud run deploy llm-infrastructure \
  --image gcr.io/PROJECT_ID/llm-infrastructure:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --timeout 3600 \
  --set-env-vars INSTANCE_CONNECTION_NAME=PROJECT_ID:us-central1:llm-infrastructure
```

---

## Azure Deployment (App Service + SQL Database)

### 1. Create Resource Group

```bash
az group create --name llm-rg --location eastus
```

### 2. Create App Service Plan

```bash
az appservice plan create \
  --name llm-plan \
  --resource-group llm-rg \
  --sku B1 --is-linux
```

### 3. Create Web App

```bash
az webapp create \
  --resource-group llm-rg \
  --plan llm-plan \
  --name llm-app \
  --deployment-container-image-name-user myregistry.azurecr.io/llm-infrastructure:latest
```

### 4. Configure Environment Variables

```bash
az webapp config appsettings set \
  --resource-group llm-rg \
  --name llm-app \
  --settings \
  WEBSITES_ENABLE_APP_SERVICE_STORAGE=true \
  NEXT_PUBLIC_COMPLIANCE_API_URL=https://api.yourdomain.com:5000 \
  NEXT_PUBLIC_DRIFT_API_URL=https://api.yourdomain.com:5001
```

---

## Production Best Practices

### 1. Security

- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Use environment variables for all secrets
- [ ] Enable API authentication/API keys
- [ ] Configure firewall rules
- [ ] Regular security audits
- [ ] Keep dependencies updated

### 2. Performance

- [ ] Set up CDN for static assets
- [ ] Configure caching headers
- [ ] Enable GZIP compression
- [ ] Use connection pooling
- [ ] Monitor database performance
- [ ] Set up auto-scaling

### 3. Monitoring

- [ ] Configure error tracking (Sentry, DataDog)
- [ ] Set up log aggregation (ELK, CloudWatch)
- [ ] Create dashboards for key metrics
- [ ] Set up alerting for anomalies
- [ ] Regular health checks
- [ ] Performance monitoring

### 4. Backup & Recovery

- [ ] Daily database backups
- [ ] Off-site backup storage
- [ ] Regular backup restoration tests
- [ ] Disaster recovery plan
- [ ] RTO/RPO targets defined

### 5. Maintenance

- [ ] Document deployment procedures
- [ ] Version all releases
- [ ] Maintain changelog
- [ ] Plan for zero-downtime deployments
- [ ] Regular dependency updates
- [ ] Security patch management

---

## Monitoring & Logging

### Application Logging

**Backend Logs:**
```bash
docker logs -f llm-compliance-api
docker logs -f llm-drift-api
```

**Frontend Logs:**
```bash
docker logs -f llm-dashboard
```

### Health Checks

```bash
# Check Compliance API
curl http://localhost:5000/health

# Check Drift API
curl http://localhost:5001/health

# Check Dashboard
curl http://localhost:3000/
```

### Metrics to Monitor

- Request latency (p50, p95, p99)
- Error rates by endpoint
- Database query times
- SSE connection count
- Memory usage
- CPU utilization
- Disk usage

---

## Scaling Considerations

### Horizontal Scaling

- Use load balancer to distribute traffic
- Stateless API design allows multiple instances
- Use shared database (SQLite → PostgreSQL for production)
- Configure session affinity if needed

### Vertical Scaling

- Increase memory/CPU for resource-intensive operations
- Database performance tuning
- Query optimization

### Database Scaling

For production, migrate from SQLite to PostgreSQL:

```sql
-- Create tables in PostgreSQL
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  -- ... other fields
);

CREATE TABLE drift_alerts (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  -- ... other fields
);
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Database Lock Issues

```bash
# For SQLite, close all connections and restart
docker compose restart compliance-api drift-api
```

### High Memory Usage

```bash
# Monitor memory
docker stats

# Increase container limits
docker run -m 2g <image>
```

### SSE Connection Issues

- Check firewall allows WebSocket upgrades
- Verify reverse proxy forwards SSE correctly
- Monitor connection timeouts

---

## Rollback Procedures

### Docker Rollback
```bash
# Pull previous image version
docker pull myregistry.azurecr.io/llm-infrastructure:v1.0.0

# Stop current service
docker compose down

# Update docker-compose.yml to use v1.0.0
# Restart service
docker compose up -d
```

### Kubernetes Rollback
```bash
# View rollout history
kubectl rollout history deployment/llm-dashboard -n llm-infrastructure

# Rollback to previous version
kubectl rollout undo deployment/llm-dashboard -n llm-infrastructure

# Rollback to specific revision
kubectl rollout undo deployment/llm-dashboard --to-revision=2 -n llm-infrastructure
```

---

## Support & Resources

- Documentation: See `docs/` directory
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@yourdomain.com

---

**Last Updated:** 2026-01-14  
**Version:** 1.0.0
