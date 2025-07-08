# Deployment Guide

## Overview

This guide covers deploying the Hybrid AI-Human System across different environments, from local development to production-scale deployments. The system is designed to be deployment-agnostic and can run on various platforms.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Deployment](#local-development-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Production Considerations](#production-considerations)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **CPU**: 2-4 cores minimum (8+ cores for production)
- **Memory**: 4GB minimum (16GB+ for production with local models)
- **Storage**: 20GB minimum (100GB+ for production with model storage)
- **Network**: Stable internet connection for cloud LLM providers

### Software Dependencies
- **Docker** 20.10+ and Docker Compose 2.0+
- **Python** 3.11+ (for local development)
- **Git** for source code management
- **Make** for build automation (optional but recommended)

### Required Services
- **Database**: SQLite (included) or PostgreSQL for production
- **Monitoring**: LangSmith account (optional)
- **Load Balancer**: Nginx or cloud load balancer for production
- **Secret Management**: Kubernetes secrets, AWS Secrets Manager, etc.

## Local Development Deployment

### Quick Start
```bash
# Clone the repository
git clone [repository-url]
cd hybrid-ai-system

# Setup with make (recommended)
make setup

# Or manual setup
cp .env.example .env
# Edit .env with your API keys
uv sync --dev

# Run the system
make run
```

### Development with Dev Container
```bash
# Open in VSCode/Cursor
code .
# Click "Reopen in Container" when prompted

# Or manually with Docker
docker-compose -f .devcontainer/docker-compose.yml up -d
docker exec -it hybrid-ai-system bash
```

### Running Components Separately
```bash
# Run main application
uv run python -m src.main

# Run Jupyter Lab for development
jupyter lab --ip=0.0.0.0 --port=8888

# Run tests
make test

# Run with specific configuration
uv run python -m src.main --config-path config/development/
```

## Docker Deployment

### Single Container Deployment
```bash
# Build the image
docker build -t hybrid-ai-system .

# Run with environment file
docker run --env-file .env -p 8888:8888 hybrid-ai-system

# Run with custom configuration
docker run \
  --env-file .env \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -p 8888:8888 \
  hybrid-ai-system
```

### Docker Compose Deployment
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  ai-system:
    build: .
    ports:
      - "8888:8888"
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
      - ./models:/app/models:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - ai-system
    restart: unless-stopped

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# Scale the application
docker-compose up -d --scale ai-system=3

# View logs
docker-compose logs -f ai-system

# Update deployment
docker-compose pull
docker-compose up -d
```

### Multi-Stage Production Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim as production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python environment
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser main.py ./

# Create necessary directories
RUN mkdir -p data logs && chown appuser:appuser data logs

USER appuser

EXPOSE 8000 8888

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "src.main"]
```

## Cloud Deployment

### AWS Deployment with ECS

#### Task Definition
```json
{
  "family": "hybrid-ai-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "ai-system",
      "image": "your-account.dkr.ecr.region.amazonaws.com/hybrid-ai-system:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/hybrid-ai-system",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Hybrid AI-Human System Infrastructure'

Parameters:
  VpcId:
    Type: AWS::EC2::VPC::Id
  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
  ImageUri:
    Type: String
    Description: ECR image URI

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: hybrid-ai-system-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  ECSService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      ServiceName: hybrid-ai-system-service
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref SecurityGroup
          Subnets: !Ref SubnetIds
          AssignPublicIp: ENABLED
      LoadBalancers:
        - ContainerName: ai-system
          ContainerPort: 8000
          TargetGroupArn: !Ref TargetGroup

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Scheme: internet-facing
      Subnets: !Ref SubnetIds
      SecurityGroups:
        - !Ref ALBSecurityGroup

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref VpcId
      TargetType: ip
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
```

### Azure Container Instances
```yaml
# azure-deployment.yml
apiVersion: 2019-12-01
location: eastus
name: hybrid-ai-system
properties:
  containers:
  - name: ai-system
    properties:
      image: your-registry.azurecr.io/hybrid-ai-system:latest
      ports:
      - port: 8000
        protocol: TCP
      resources:
        requests:
          cpu: 1.0
          memoryInGB: 2.0
      environmentVariables:
      - name: ENVIRONMENT
        value: production
      - name: OPENAI_API_KEY
        secureValue: your-api-key
  osType: Linux
  restartPolicy: Always
  dnsConfig:
    nameServers:
    - 8.8.8.8
  networkProfile:
    id: /subscriptions/subscription-id/resourceGroups/rg/providers/Microsoft.Network/networkProfiles/networkProfile
tags:
  environment: production
  application: hybrid-ai-system
type: Microsoft.ContainerInstance/containerGroups
```

### Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/hybrid-ai-system

# Deploy to Cloud Run
gcloud run deploy hybrid-ai-system \
  --image gcr.io/PROJECT_ID/hybrid-ai-system \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

## Kubernetes Deployment

### Namespace and ConfigMap
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hybrid-ai-system
  labels:
    name: hybrid-ai-system

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-system-config
  namespace: hybrid-ai-system
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  models.yaml: |
    default_model: "gpt-4"
    fallback_models: ["claude-3-sonnet"]
  config.json: |
    {
      "thresholds": {
        "escalation_score": 7.0
      }
    }
```

### Secrets
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-system-secrets
  namespace: hybrid-ai-system
type: Opaque
stringData:
  OPENAI_API_KEY: "your-openai-key"
  ANTHROPIC_API_KEY: "your-anthropic-key"
  LANGCHAIN_API_KEY: "your-langsmith-key"
```

### Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hybrid-ai-system
  namespace: hybrid-ai-system
  labels:
    app: hybrid-ai-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hybrid-ai-system
  template:
    metadata:
      labels:
        app: hybrid-ai-system
    spec:
      containers:
      - name: ai-system
        image: your-registry/hybrid-ai-system:latest
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: ai-system-config
        - secretRef:
            name: ai-system-secrets
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        - name: data-volume
          mountPath: /app/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: ai-system-config
          items:
          - key: models.yaml
            path: models.yaml
          - key: config.json
            path: config.json
      - name: data-volume
        persistentVolumeClaim:
          claimName: ai-system-data-pvc
```

### Service and Ingress
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: hybrid-ai-system-service
  namespace: hybrid-ai-system
spec:
  selector:
    app: hybrid-ai-system
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hybrid-ai-system-ingress
  namespace: hybrid-ai-system
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - ai-system.yourdomain.com
    secretName: ai-system-tls
  rules:
  - host: ai-system.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hybrid-ai-system-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hybrid-ai-system-hpa
  namespace: hybrid-ai-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hybrid-ai-system
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deployment Commands
```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n hybrid-ai-system
kubectl get svc -n hybrid-ai-system
kubectl get ing -n hybrid-ai-system

# View logs
kubectl logs -n hybrid-ai-system deployment/hybrid-ai-system -f

# Scale deployment
kubectl scale deployment hybrid-ai-system --replicas=5 -n hybrid-ai-system

# Rolling update
kubectl set image deployment/hybrid-ai-system ai-system=your-registry/hybrid-ai-system:new-tag -n hybrid-ai-system

# Rollback if needed
kubectl rollout undo deployment/hybrid-ai-system -n hybrid-ai-system
```

## Production Considerations

### Security
```bash
# Use non-root user in containers
USER 1001

# Read-only filesystem where possible
securityContext:
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1001

# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-system-netpol
spec:
  podSelector:
    matchLabels:
      app: hybrid-ai-system
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### Resource Management
```yaml
# Resource quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ai-system-quota
  namespace: hybrid-ai-system
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    persistentvolumeclaims: "3"
```

### High Availability
```yaml
# Pod Disruption Budget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ai-system-pdb
  namespace: hybrid-ai-system
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: hybrid-ai-system
```

### Performance Tuning
```bash
# CPU limits for optimal performance
resources:
  requests:
    cpu: "1000m"
    memory: "2Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"

# JVM tuning for better performance
env:
- name: PYTHON_OPTS
  value: "-O"
```

## Monitoring and Observability

### Health Checks
```python
# Health check endpoint
@app.route('/health')
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.config.get('VERSION'),
        "checks": {
            "database": check_database(),
            "llm_providers": check_llm_providers(),
            "memory_usage": get_memory_usage()
        }
    }
```

### Prometheus Metrics
```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: hybrid-ai-system-metrics
  namespace: hybrid-ai-system
spec:
  selector:
    matchLabels:
      app: hybrid-ai-system
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Hybrid AI-Human System",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### Log Aggregation
```yaml
# Fluentd configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*hybrid-ai-system*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
      read_from_head true
    </source>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name hybrid-ai-system
    </match>
```

## Backup and Recovery

### Database Backup
```bash
# SQLite backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/app/data/hybrid_system.db"

# Create backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/hybrid_system_$DATE.db"

# Compress backup
gzip "$BACKUP_DIR/hybrid_system_$DATE.db"

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "hybrid_system_*.db.gz" -mtime +30 -delete
```

### Kubernetes Backup
```yaml
# Velero backup schedule
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: hybrid-ai-system-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  template:
    includedNamespaces:
    - hybrid-ai-system
    storageLocation: default
    ttl: 720h0m0s  # 30 days
```

### Configuration Backup
```bash
# Backup configuration and secrets
kubectl get configmap ai-system-config -n hybrid-ai-system -o yaml > config-backup.yaml
kubectl get secret ai-system-secrets -n hybrid-ai-system -o yaml > secrets-backup.yaml
```

## Troubleshooting

### Common Issues

#### Pod Crashes
```bash
# Check pod status
kubectl get pods -n hybrid-ai-system
kubectl describe pod <pod-name> -n hybrid-ai-system

# Check logs
kubectl logs <pod-name> -n hybrid-ai-system --previous

# Check resource usage
kubectl top pods -n hybrid-ai-system
```

#### Service Discovery Issues
```bash
# Test service connectivity
kubectl run test-pod --image=busybox -it --rm --restart=Never -- nslookup hybrid-ai-system-service.hybrid-ai-system.svc.cluster.local

# Check endpoints
kubectl get endpoints -n hybrid-ai-system
```

#### Configuration Issues
```bash
# Validate configuration
kubectl exec -it <pod-name> -n hybrid-ai-system -- python -c "from src.core.config import ConfigManager; ConfigManager('config')"

# Check mounted volumes
kubectl exec -it <pod-name> -n hybrid-ai-system -- ls -la /app/config
```

### Performance Issues
```bash
# Monitor resource usage
kubectl top pods -n hybrid-ai-system
kubectl top nodes

# Check HPA status
kubectl get hpa -n hybrid-ai-system

# Analyze logs for bottlenecks
kubectl logs -n hybrid-ai-system deployment/hybrid-ai-system | grep "slow\|timeout\|error"
```

### Debugging Tools
```yaml
# Debug pod for troubleshooting
apiVersion: v1
kind: Pod
metadata:
  name: debug-pod
  namespace: hybrid-ai-system
spec:
  containers:
  - name: debug
    image: nicolaka/netshoot
    command: ["/bin/bash"]
    args: ["-c", "while true; do ping localhost; sleep 30;done"]
    envFrom:
    - configMapRef:
        name: ai-system-config
    - secretRef:
        name: ai-system-secrets
```

### Recovery Procedures
```bash
# Rollback deployment
kubectl rollout undo deployment/hybrid-ai-system -n hybrid-ai-system

# Restore from backup
kubectl apply -f config-backup.yaml
kubectl apply -f secrets-backup.yaml

# Force pod recreation
kubectl delete pods -l app=hybrid-ai-system -n hybrid-ai-system
```

This deployment guide provides comprehensive coverage for deploying the Hybrid AI-Human System across various environments and platforms, with production-ready configurations and troubleshooting guidance.