# User Guide

Guide for managing multi-user environments and provisioning new users.

## Multi-User Architecture

Each user gets:
- Dedicated Kubernetes namespace
- Private Home Assistant instance
- Dedicated Ollama instance with GPU access
- Resource quotas and limits
- Isolated storage
- Custom ingress endpoints

## User Provisioning

### Create New User

```bash
# Provision user with script
./scripts/user-provision.sh john-doe

# This creates:
# - Namespace: ha-llm-user-john-doe
# - Resource quotas
# - HA + Ollama deployments
# - Ingress rules
# - Service account
# - Kubeconfig file
```

### Manual Provisioning

```bash
# 1. Create namespace
kubectl create namespace ha-llm-user-john-doe

# 2. Apply resource quota
kubectl apply -f kubernetes/namespaces/resourcequota.yaml -n ha-llm-user-john-doe

# 3. Deploy HA-LLM stack
helm install ha-llm-john-doe ./helm/ha-llm-stack \
  --namespace ha-llm-user-john-doe \
  --set global.domain="john-doe.yourdomain.com"

# 4. Create service account and RBAC
kubectl create serviceaccount john-doe -n ha-llm-user-john-doe
kubectl create rolebinding john-doe-admin \
  --clusterrole=admin \
  --serviceaccount=ha-llm-user-john-doe:john-doe \
  -n ha-llm-user-john-doe
```

## User Access

### Providing Access to Users

Each user receives:
1. **URLs**:
   - Home Assistant: `https://ha.username.yourdomain.com`
   - Ollama API: `https://ollama.username.yourdomain.com`

2. **Kubeconfig** (optional):
   ```bash
   export KUBECONFIG=username-kubeconfig.yaml
   kubectl get pods
   ```

3. **Credentials**:
   - Home Assistant: Set up during first access
   - API tokens: Generated in Home Assistant

### User Onboarding Checklist

- [ ] Provision user namespace
- [ ] Configure resource quotas
- [ ] Deploy services
- [ ] Set up ingress/DNS
- [ ] Generate access credentials
- [ ] Send welcome email with:
  - Access URLs
  - Initial setup instructions
  - Support contact
  - Resource limits

## Resource Management

### Default Resource Quotas

Per user namespace:
```yaml
requests:
  cpu: "4"
  memory: 8Gi
  nvidia.com/gpu: "1"
limits:
  cpu: "8"
  memory: 16Gi
  nvidia.com/gpu: "1"
storage: "100Gi"
```

### Adjusting User Resources

```bash
# Edit resource quota
kubectl edit resourcequota user-quota -n ha-llm-user-john-doe

# Or apply custom quota
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: user-quota
  namespace: ha-llm-user-john-doe
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    requests.nvidia.com/gpu: "2"
EOF
```

### Monitoring Resource Usage

```bash
# View namespace resource usage
kubectl top pods -n ha-llm-user-john-doe
kubectl top nodes

# Check quota usage
kubectl describe resourcequota user-quota -n ha-llm-user-john-doe

# View all user namespaces
kubectl get namespaces -l user-namespace=true
```

## User Management Operations

### List All Users

```bash
# List all user namespaces
kubectl get namespaces -l user-namespace=true

# Get user details
kubectl get all -n ha-llm-user-john-doe
```

### Suspend User

```bash
# Scale down user deployments
kubectl scale deployment --all --replicas=0 -n ha-llm-user-john-doe

# Optional: Remove ingress
kubectl delete ingress --all -n ha-llm-user-john-doe
```

### Resume User

```bash
# Scale up deployments
kubectl scale deployment/home-assistant --replicas=1 -n ha-llm-user-john-doe
kubectl scale deployment/ollama --replicas=1 -n ha-llm-user-john-doe

# Restore ingress
helm upgrade ha-llm-john-doe ./helm/ha-llm-stack \
  --namespace ha-llm-user-john-doe \
  --reuse-values
```

### Delete User

```bash
# Remove Helm release
helm uninstall ha-llm-john-doe -n ha-llm-user-john-doe

# Delete namespace (removes all resources)
kubectl delete namespace ha-llm-user-john-doe

# Clean up DNS records
# ...
```

## Ollama Model Management

### Pre-load Models for User

```bash
# Get Ollama pod
OLLAMA_POD=$(kubectl get pod -n ha-llm-user-john-doe -l app.kubernetes.io/component=ollama -o jsonpath='{.items[0].metadata.name}')

# Pull models
kubectl exec -n ha-llm-user-john-doe $OLLAMA_POD -- ollama pull llama3:8b
kubectl exec -n ha-llm-user-john-doe $OLLAMA_POD -- ollama pull mistral:7b

# List available models
kubectl exec -n ha-llm-user-john-doe $OLLAMA_POD -- ollama list
```

### User-Initiated Model Downloads

Users can pull models via Ollama API:

```bash
curl https://ollama.username.yourdomain.com/api/pull \
  -d '{"name": "llama3:8b"}'
```

Or from Home Assistant:
```yaml
# configuration.yaml
rest_command:
  pull_ollama_model:
    url: "http://ollama:11434/api/pull"
    method: POST
    payload: '{"name": "{{ model }}"}'
```

## GPU Allocation

### GPU Sharing Strategies

**Option 1: Dedicated GPU per User**
- Each user gets full GPU
- Best performance
- Limited user count

**Option 2: Time-Slicing**
- Multiple users share GPU
- NVIDIA MIG or time-slicing
- More users, potential performance impact

**Option 3: GPU Pool**
- Dynamic GPU allocation
- Users request GPU on-demand
- Complex scheduling

### Monitor GPU Usage

```bash
# View GPU allocation
kubectl describe node gpu-node-1 | grep -A 5 "Allocated resources"

# Check GPU usage per pod
kubectl exec -n ha-llm-user-john-doe $OLLAMA_POD -- nvidia-smi
```

## Storage Management

### Backup User Data

```bash
# Create volume snapshot
kubectl create volumesnapshot user-backup \
  --volume=home-assistant-config \
  --namespace=ha-llm-user-john-doe

# Export user configuration
kubectl exec -n ha-llm-user-john-doe $HA_POD -- tar czf - /config > user-backup.tar.gz
```

### Expand User Storage

```bash
# Edit PVC (if storage class supports expansion)
kubectl patch pvc home-assistant-config \
  -n ha-llm-user-john-doe \
  -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

## Troubleshooting User Issues

### User Cannot Access Service

```bash
# Check pod status
kubectl get pods -n ha-llm-user-john-doe

# Check ingress
kubectl get ingress -n ha-llm-user-john-doe
kubectl describe ingress -n ha-llm-user-john-doe

# Check DNS
nslookup ha.username.yourdomain.com

# Check certificate
kubectl get certificate -n ha-llm-user-john-doe
```

### User Experiencing Slow Performance

```bash
# Check resource usage
kubectl top pods -n ha-llm-user-john-doe

# Check resource quotas
kubectl describe resourcequota -n ha-llm-user-john-doe

# Check GPU
kubectl exec -n ha-llm-user-john-doe $OLLAMA_POD -- nvidia-smi

# View logs
kubectl logs -n ha-llm-user-john-doe $OLLAMA_POD --tail=100
```

### User Out of Storage

```bash
# Check PVC usage
kubectl exec -n ha-llm-user-john-doe $HA_POD -- df -h

# Clean up old models
kubectl exec -n ha-llm-user-john-doe $OLLAMA_POD -- ollama rm old-model

# Expand storage (see above)
```

## Best Practices

1. **Resource Planning**
   - Calculate user capacity based on GPU count
   - Monitor resource utilization
   - Set appropriate quotas

2. **Security**
   - Isolate user namespaces
   - Use NetworkPolicies
   - Regular security audits
   - Rotate credentials

3. **Performance**
   - Pre-load common models
   - Use appropriate GPU types
   - Monitor and optimize

4. **Documentation**
   - Maintain user documentation
   - Document custom configurations
   - Keep runbooks updated

5. **Communication**
   - Notify users of maintenance
   - Provide support channels
   - Collect user feedback
