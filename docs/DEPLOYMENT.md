# Deployment Guide

Production deployment strategies and best practices.

## Deployment Strategies

### Blue-Green Deployment

```bash
# Deploy new version (green)
helm install ha-llm-stack-green ./helm/ha-llm-stack \
  --namespace ha-llm-green \
  --create-namespace \
  --values ./helm/ha-llm-stack/values-prod.yaml

# Test green deployment
kubectl port-forward -n ha-llm-green svc/home-assistant 8124:8123

# Switch traffic (update ingress or load balancer)
# ...

# Remove old deployment (blue)
helm uninstall ha-llm-stack -n ha-llm-system
```

### Rolling Updates

```bash
# Update with Helm (default strategy)
helm upgrade ha-llm-stack ./helm/ha-llm-stack \
  --namespace ha-llm-system \
  --values ./helm/ha-llm-stack/values-prod.yaml \
  --wait

# Monitor rollout
kubectl rollout status deployment/home-assistant -n ha-llm-system
```

### Canary Deployment

Use Istio or similar service mesh for advanced traffic splitting.

## CI/CD Pipeline

### GitHub Actions Setup

1. **Configure Secrets**:
   - `KUBECONFIG_DEV`: Development cluster config
   - `KUBECONFIG_PROD`: Production cluster config
   - `SLACK_WEBHOOK`: Notification webhook
   - `GITHUB_TOKEN`: Automatic (provided by GitHub)

2. **Branch Strategy**:
   - `main`: Production releases
   - `develop`: Development/staging
   - `feature/*`: Feature branches

3. **Workflow Triggers**:
   - Push to `develop` → Auto-deploy to dev
   - Release published → Manual approval → Deploy to prod
   - Pull requests → Build and test only

### Manual Deployment

```bash
# Build Docker images
docker build -t myregistry/home-assistant:v1.0.0 ./docker/home-assistant
docker build -t myregistry/ollama:v1.0.0 ./docker/ollama

# Push to registry
docker push myregistry/home-assistant:v1.0.0
docker push myregistry/ollama:v1.0.0

# Update values.yaml with new image tags
# Deploy with Helm
helm upgrade ha-llm-stack ./helm/ha-llm-stack \
  --namespace ha-llm-system \
  --values ./helm/ha-llm-stack/values-prod.yaml \
  --set homeAssistant.image.tag=v1.0.0 \
  --set ollama.image.tag=v1.0.0
```

## Production Checklist

### Pre-Deployment

- [ ] Backup current deployment
- [ ] Review change logs
- [ ] Test in staging environment
- [ ] Verify resource availability
- [ ] Check GPU node availability
- [ ] Confirm monitoring is operational
- [ ] Schedule maintenance window

### Deployment

- [ ] Deploy to production
- [ ] Monitor pod startup
- [ ] Verify health checks pass
- [ ] Test critical functionality
- [ ] Check monitoring dashboards
- [ ] Verify GPU allocation

### Post-Deployment

- [ ] Monitor for errors (24h)
- [ ] Verify user access
- [ ] Check performance metrics
- [ ] Update documentation
- [ ] Notify stakeholders
- [ ] Tag release in Git

## Rollback Procedures

### Helm Rollback

```bash
# View release history
helm history ha-llm-stack -n ha-llm-system

# Rollback to previous version
helm rollback ha-llm-stack -n ha-llm-system

# Rollback to specific revision
helm rollback ha-llm-stack 3 -n ha-llm-system
```

### Kubernetes Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/home-assistant -n ha-llm-system
kubectl rollout undo deployment/ollama -n ha-llm-system

# Rollback to specific revision
kubectl rollout undo deployment/home-assistant --to-revision=2 -n ha-llm-system
```

## Scaling

### Horizontal Scaling

Home Assistant can be scaled (with proper configuration):

```bash
kubectl scale deployment/home-assistant --replicas=3 -n ha-llm-system
```

Or with Helm:

```yaml
# values-prod.yaml
homeAssistant:
  replicas: 3
```

### Vertical Scaling

Adjust resource limits:

```yaml
# values-prod.yaml
homeAssistant:
  resources:
    requests:
      memory: "2Gi"
      cpu: "2000m"
    limits:
      memory: "8Gi"
      cpu: "8000m"
```

### GPU Scaling

Add more GPU nodes or adjust GPU allocation:

```bash
# Terraform
terraform apply -var="gpu_node_count=5"
```

## Multi-Region Deployment

For global availability:

1. Deploy to multiple regions
2. Use global load balancer
3. Replicate storage (if needed)
4. Configure DNS for failover

## Disaster Recovery

### Backup Strategy

```bash
# Backup Helm release
helm get values ha-llm-stack -n ha-llm-system > backup-values.yaml
helm get manifest ha-llm-stack -n ha-llm-system > backup-manifest.yaml

# Backup persistent data
kubectl get pvc -n ha-llm-system
# Use volume snapshots or backup tools

# Backup configuration
kubectl get configmap -n ha-llm-system -o yaml > backup-configmaps.yaml
kubectl get secret -n ha-llm-system -o yaml > backup-secrets.yaml
```

### Restore Procedure

```bash
# Restore namespace
kubectl create namespace ha-llm-system

# Restore secrets and configmaps
kubectl apply -f backup-secrets.yaml
kubectl apply -f backup-configmaps.yaml

# Restore with Helm
helm install ha-llm-stack ./helm/ha-llm-stack \
  --namespace ha-llm-system \
  --values backup-values.yaml

# Restore persistent volumes (provider-specific)
# ...
```

## Monitoring and Alerting

### Key Metrics to Monitor

- Pod health and restart count
- Resource utilization (CPU, Memory, GPU)
- API response times
- Error rates
- GPU temperature and utilization
- Storage usage

### Alerting Rules

Configure alerts for:
- Service down (> 5 minutes)
- High error rate (> 5% in 5 minutes)
- Resource exhaustion (> 90% for 10 minutes)
- GPU issues (temperature, memory)
- Certificate expiration (< 30 days)

## Security Hardening

- Enable Pod Security Standards
- Use Network Policies
- Rotate secrets regularly
- Enable audit logging
- Use private container registry
- Scan images for vulnerabilities
- Limit resource access with RBAC
- Enable TLS everywhere

## Performance Optimization

### Ollama Performance

- Use appropriate GPU types (V100, A100)
- Allocate sufficient GPU memory
- Consider model quantization
- Use model caching
- Monitor inference latency

### Storage Optimization

- Use SSD-backed storage
- Enable volume snapshots
- Implement retention policies
- Monitor IOPS usage

### Network Optimization

- Use service mesh for traffic management
- Enable HTTP/2
- Configure appropriate timeouts
- Use connection pooling
