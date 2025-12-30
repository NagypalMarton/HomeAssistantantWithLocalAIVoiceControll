# Home Assistant + Local LLM DevOps Project

Multi-user Home Assistant installation with locally running Ollama LLM models, powered by NVIDIA GPUs.

## 🏗️ Architecture

This project provides a complete DevOps pipeline for running Home Assistant with Ollama LLM in a multi-user Kubernetes environment.

**Components:**
- **Home Assistant**: Smart home automation platform
- **Ollama**: Local LLM inference with NVIDIA GPU support
- **Kubernetes**: Container orchestration with GPU node pools
- **Helm**: Package management and multi-environment deployment
- **Terraform**: Infrastructure as Code for cluster provisioning
- **GitHub Actions**: CI/CD pipeline
- **Zabbix**: Monitoring and alerting

## 📋 Prerequisites

### Local Development
- Docker & Docker Compose
- NVIDIA GPU with drivers (optional for dev)
- 16GB+ RAM recommended
- 100GB+ free disk space for models

### Production
- Kubernetes cluster (1.28+)
- NVIDIA GPU nodes (Tesla T4, V100, or better)
- kubectl & Helm 3
- Terraform 1.5+
- Domain name with DNS access

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd HomeAssistantantWithLocalAIVoiceControll

# Setup local environment
chmod +x scripts/setup-local.sh
./scripts/setup-local.sh
```

Access services:
- Home Assistant: http://localhost:8123
- Zabbix: http://localhost:8080 (Admin/zabbix)
- Ollama API: http://localhost:11434

### Kubernetes Deployment

```bash
# Deploy to development
./scripts/deploy-k8s.sh dev

# Deploy to production
./scripts/deploy-k8s.sh prod
```

## 📚 Documentation

Detailed documentation available in the `docs/` directory:

- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Deployment Guide](docs/DEPLOYMENT.md) - Kubernetes deployment
- [User Guide](docs/USER_GUIDE.md) - Multi-user provisioning
- [Architecture](docs/ARCHITECTURE.md) - System design and components

## 🔧 Project Structure

```
.
├── docker/                  # Docker configurations
│   ├── docker-compose.yml
│   ├── home-assistant/
│   └── ollama/
├── kubernetes/              # Raw Kubernetes manifests
│   ├── namespaces/
│   ├── home-assistant/
│   ├── ollama/
│   └── ingress/
├── helm/                    # Helm charts
│   └── ha-llm-stack/
├── terraform/               # Infrastructure as Code
│   ├── modules/
│   └── environments/
├── .github/workflows/       # CI/CD pipelines
├── monitoring/              # Zabbix configuration
│   └── zabbix/
├── config/                  # Application configs
├── scripts/                 # Utility scripts
└── docs/                    # Documentation
```

## 🔐 Security

- Store secrets in Kubernetes Secrets or external secret managers
- Enable RBAC for multi-user isolation
- Use TLS certificates (cert-manager)
- Configure network policies
- Regular security scans with Trivy

## 📊 Monitoring

Zabbix monitors:
- Home Assistant availability and response time
- Ollama API health and model availability
- GPU utilization and memory
- Kubernetes resource usage
- Custom alerts and dashboards

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- GitHub Issues: [Create an issue](../../issues)
- Documentation: [docs/](docs/)
- Community: [Discussions](../../discussions)

## 🎯 Roadmap

- [ ] Multi-cloud Terraform modules (AWS, Azure, GCP)
- [ ] Advanced GPU sharing and scheduling
- [ ] Grafana dashboards
- [ ] Voice integration examples
- [ ] Model fine-tuning pipeline
- [ ] Backup and disaster recovery automation
- [ ] Cost optimization strategies

---

**Note**: This project requires NVIDIA GPUs for optimal Ollama performance. CPU-only mode is available but significantly slower.
