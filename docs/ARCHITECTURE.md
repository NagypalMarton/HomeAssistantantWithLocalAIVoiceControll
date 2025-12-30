# Architecture Documentation

## System Overview

The Home Assistant + Ollama LLM stack is designed as a multi-tenant, containerized platform that provides each user with isolated instances of Home Assistant and Ollama LLM services.

## Components

### 1. Home Assistant
- **Purpose**: Smart home automation and control
- **Deployment**: Kubernetes Deployment with persistent storage
- **Resources**: Configurable CPU/Memory
- **Networking**: ClusterIP service + Ingress
- **Storage**: 5-10GB PersistentVolume per user

### 2. Ollama
- **Purpose**: Local LLM inference
- **Deployment**: Kubernetes Deployment with GPU support
- **Resources**: GPU required, configurable memory
- **Models**: llama3, mistral, codellama, etc.
- **Storage**: 50-100GB PersistentVolume for models
- **API**: REST API on port 11434

### 3. Kubernetes Infrastructure
- **Orchestration**: Kubernetes 1.28+
- **Namespace Isolation**: One namespace per user
- **Resource Management**: ResourceQuota and LimitRange
- **GPU Support**: NVIDIA Device Plugin
- **Storage**: PersistentVolumes with dynamic provisioning
- **Networking**: Ingress NGINX + cert-manager for TLS

### 4. CI/CD Pipeline
- **Platform**: GitHub Actions
- **Stages**:
  - Build: Docker image creation
  - Test: Validation and security scanning
  - Deploy: Automated deployment to dev/prod
- **Container Registry**: GitHub Container Registry (GHCR)

### 5. Infrastructure as Code
- **Tool**: Terraform
- **Manages**:
  - Kubernetes cluster provisioning
  - GPU node pools
  - Storage classes
  - Network configuration
- **Environments**: Dev, Staging, Production

### 6. Monitoring
- **Platform**: Zabbix
- **Metrics**:
  - Service availability
  - Response times
  - GPU utilization
  - Resource consumption
- **Alerting**: Email, Slack, custom webhooks

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Users/Clients                         │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ingress Controller                        │
│                    (NGINX + cert-manager)                    │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   User Namespace 1      │       │   User Namespace 2      │
│  ┌─────────────────┐    │       │  ┌─────────────────┐    │
│  │ Home Assistant  │    │       │  │ Home Assistant  │    │
│  │   Deployment    │    │       │  │   Deployment    │    │
│  └────────┬────────┘    │       │  └────────┬────────┘    │
│           │             │       │           │             │
│           │ REST API    │       │           │ REST API    │
│           ▼             │       │           ▼             │
│  ┌─────────────────┐    │       │  ┌─────────────────┐    │
│  │     Ollama      │    │       │  │     Ollama      │    │
│  │   Deployment    │    │       │  │   Deployment    │    │
│  │   (+ GPU)       │    │       │  │   (+ GPU)       │    │
│  └─────────────────┘    │       │  └─────────────────┘    │
│                         │       │                         │
│  ┌─────────────────┐    │       │  ┌─────────────────┐    │
│  │ Persistent      │    │       │  │ Persistent      │    │
│  │ Storage         │    │       │  │ Storage         │    │
│  └─────────────────┘    │       │  └─────────────────┘    │
└─────────────────────────┘       └─────────────────────────┘
                │                             │
                └─────────────┬───────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │      GPU Node Pool          │
                │  (NVIDIA T4/V100/A100)      │
                └─────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │     Monitoring Stack        │
                │         (Zabbix)            │
                └─────────────────────────────┘
```

## Data Flow

### 1. User Request Flow
1. User accesses `https://ha.username.domain.com`
2. Ingress controller routes to user's namespace
3. Request reaches Home Assistant service
4. Home Assistant processes request
5. Response returns through same path

### 2. LLM Inference Flow
1. Home Assistant sends prompt to Ollama API
2. Ollama loads model from storage
3. GPU processes inference
4. Ollama returns generated text
5. Home Assistant uses result

### 3. Deployment Flow
1. Code pushed to GitHub
2. GitHub Actions triggered
3. Docker images built and pushed
4. Helm chart updated
5. Kubernetes applies changes
6. Services rolled out
7. Health checks verified
8. Monitoring updated

## Security Architecture

### Network Security
- **Namespace Isolation**: NetworkPolicies restrict traffic
- **TLS Encryption**: All external traffic encrypted
- **Ingress Authentication**: Optional OAuth2/OIDC
- **Internal Communication**: Plain HTTP (within cluster)

### Access Control
- **RBAC**: Role-based access per namespace
- **Service Accounts**: Limited permissions per service
- **Pod Security**: Pod Security Standards enforced
- **Secrets Management**: Kubernetes Secrets or external vault

### GPU Security
- **Resource Isolation**: GPU time-slicing or MPS
- **Quota Enforcement**: Limits on GPU access per user
- **Monitoring**: GPU usage tracked and alerted

## Scaling Strategy

### Horizontal Scaling
- **Home Assistant**: Can scale to multiple replicas
- **Ollama**: Single replica per user (GPU bound)
- **Ingress**: Multiple replicas with load balancing

### Vertical Scaling
- **Increase Resources**: Adjust CPU/Memory/GPU allocation
- **Upgrade GPUs**: Use more powerful GPU types
- **Storage Expansion**: Expand PersistentVolumes

### Multi-Region
- **Geographic Distribution**: Deploy to multiple regions
- **Global Load Balancing**: Route users to nearest region
- **Data Replication**: Sync configuration across regions

## Storage Architecture

### Home Assistant Storage
- **Type**: PersistentVolume (RWO)
- **Size**: 5-10GB per user
- **Content**: Configuration, databases, logs
- **Backup**: Volume snapshots

### Ollama Model Storage
- **Type**: PersistentVolume (RWO)
- **Size**: 50-100GB per user
- **Content**: LLM model files
- **Optimization**: Shared model cache (optional)

### Backup Strategy
- **Frequency**: Daily
- **Retention**: 30 days
- **Method**: Volume snapshots + off-cluster backup
- **Recovery**: Restore from snapshot

## High Availability

### Component HA
- **Kubernetes Control Plane**: Multi-master setup
- **Ingress Controller**: Multiple replicas
- **Storage**: Replicated block storage
- **Database**: External managed database (optional)

### Failure Scenarios
- **Pod Failure**: Automatic restart by Kubernetes
- **Node Failure**: Pods rescheduled to healthy nodes
- **GPU Failure**: Alert and manual intervention
- **Storage Failure**: Restore from backup

## Performance Considerations

### Ollama Performance
- **GPU Selection**: V100/A100 recommended for production
- **Model Selection**: Balance size vs performance
- **Batch Processing**: Queue multiple requests
- **Caching**: Cache common prompts

### Home Assistant Performance
- **Resource Allocation**: Sufficient CPU/Memory
- **Database Optimization**: Use PostgreSQL for large setups
- **Caching**: Enable HTTP caching
- **Background Tasks**: Offload to separate workers

## Cost Optimization

### Resource Efficiency
- **Right-sizing**: Monitor and adjust resource requests
- **GPU Sharing**: Time-slicing or MIG when possible
- **Storage Tiering**: Use appropriate storage classes
- **Auto-scaling**: Scale down during low usage

### Multi-Tenancy
- **Shared Infrastructure**: Kubernetes overhead shared
- **Shared Models**: Optional shared model storage
- **Efficient Packing**: Maximize node utilization

## Technology Stack

- **Container Runtime**: containerd
- **Orchestration**: Kubernetes 1.28+
- **Service Mesh**: Optional (Istio/Linkerd)
- **Storage**: CSI-compatible storage provider
- **Networking**: CNI plugin (Calico/Cilium)
- **Monitoring**: Zabbix
- **Logging**: Optional (ELK/Loki)
- **CI/CD**: GitHub Actions
- **IaC**: Terraform
- **Package Management**: Helm 3
