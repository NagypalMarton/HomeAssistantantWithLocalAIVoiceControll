# Mikrobi - AI-Powered Smart Home System

Edge-cloud architecture for voice and text-based smart home control with LLM intelligence and Home Assistant integration.

## 🏗️ Architecture

Mikrobi is a distributed smart home system with two main layers:

**Edge Layer (Raspberry Pi 4):**
- Wake-word detection ("Mikrobi")
- Automatic Speech Recognition (ASR) - Hungarian and English
- Voice command processing
- Communication with assigned Home Assistant instance

**Central Layer (Kubernetes):**
- Backend services and user management
- Ollama LLM (Ministral 3 3B) for contextual intent processing
- Multi-user Home Assistant instances (one per user)
- Administration interface
- Monitoring and orchestration

**Key Design Principles:**
- One Raspberry Pi per user
- Edge devices communicate only via Home Assistant REST API
- No direct IoT device control from Raspberry Pi
- Request-level logical isolation for shared LLM

## 📋 System Components

### Edge Components
- **Wake-word Detection**: Continuous listening for "Mikrobi" trigger
- **ASR Service**: Speech-to-text conversion (Hungarian/English)
- **Edge Communicator**: REST API client for Home Assistant

### Central Components
- **User Management**: Registration, authentication, profile management
- **Home Assistant Instances**: Isolated per-user smart home control
- **LLM Service**: Ollama with Ministral 3 3B for contextual commands
- **Intent Processor**: Routes explicit commands directly, contextual to LLM
- **Admin UI**: System management and monitoring
- **User UI**: Login, registration, Home Assistant instance access

### Infrastructure
- **Docker**: Containerized components
- **Kubernetes**: Orchestration for central services
- **Terraform**: Infrastructure as Code for HA instances and services
- **Zabbix**: Comprehensive monitoring

## 🚀 Quick Start

### Prerequisites

**Edge Device:**
- Raspberry Pi 4 (2GB RAM minimum)
- Microphone
- Network connectivity

**Central Infrastructure:**
- Kubernetes cluster (1.28+)
- NVIDIA GPU for LLM inference
- 16GB+ RAM
- 100GB+ storage for models

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd HomeAssistantantWithLocalAIVoiceControll

# Setup central services
./scripts/setup-local.sh

# Deploy Home Assistant instance
./scripts/create-ha-instance.sh <username>
```

### Edge Device Setup

```bash
# On Raspberry Pi
./scripts/setup-edge.sh

# Configure user assignment
./scripts/configure-edge.sh --user=<username>
```

## 🎤 Voice Control

### Wake-word Activation
1. Say "Mikrobi" to activate
2. Wait for acknowledgment tone
3. Speak your command in Hungarian or English
4. System provides audio/text feedback

### Command Types

**Explicit Commands** (Direct to Home Assistant):
- "Kapcsold fel a lámpát" (Turn on the light)
- "Állítsd 22 fokra a termosztátot" (Set thermostat to 22°C)

**Contextual Commands** (Processed by LLM):
- "Sötét van a konyhában" (It's dark in the kitchen)
- "Fázom" (I'm cold)
- LLM interprets intent and suggests appropriate actions

## 💬 Text Control

Access the web interface to send text commands:
- Same intent processing as voice commands
- Full Home Assistant device control
- Automation creation with approval workflow

## 🔐 Security Features

- User authentication required
- Each user has isolated Home Assistant instance
- Security-critical operations require confirmation
- Voice and text data **not stored** (immediate deletion)
- Internet-accessible with proper authentication

## 🤖 LLM Intelligence

**Ministral 3 3B Model via Ollama:**
- Contextual command interpretation
- Access to full Home Assistant state
- Automation creation capabilities
- Logical request-level isolation

**Automation Workflow:**
1. LLM suggests automation based on command
2. User must approve before creation
3. Automation deployed to user's HA instance

## 📊 Monitoring

Zabbix monitors all system components:
- Kubernetes and Docker services
- Home Assistant API availability
- Ollama/LLM metrics and performance
- Raspberry Pi health (lightweight HTTP exporter)
- Custom alerts and dashboards

## 🔧 User Management

### Registration
- First name, last name, location, password
- Automatic Home Assistant instance creation
- Unique instance URL assigned

### Account Deletion
- Complete removal of user data
- Permanent deletion of associated HA instance

## 📈 Performance Targets

- Wake-word detection: < 500ms
- LLM response time: < 3 seconds
- System availability: 99%

## 🛠️ DevOps & Updates

**Automatic Updates:**
- Raspberry Pi OS and containers (automatic)

**Manual Updates:**
- Backend services (admin approval required)
- Kubernetes deployments

**Infrastructure:**
```bash
# Deploy infrastructure changes
cd terraform/environments/prod
terraform plan
terraform apply

# Update central services
./scripts/deploy-k8s.sh prod
```

## 📚 Documentation

- [Software Requirements Specification](mikrobi_okosotthon_rendszer_srs.md) - Complete system specification
- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Edge Device Guide](docs/EDGE_SETUP.md) - Raspberry Pi setup
- [Architecture Details](docs/ARCHITECTURE.md) - System design

## 🎯 Key Features

✅ Wake-word activated voice control  
✅ Multi-language support (Hungarian, English)  
✅ LLM-powered contextual understanding  
✅ One-to-one edge-to-user mapping  
✅ Isolated Home Assistant instances  
✅ Automation creation with approval  
✅ Text and voice control parity  
✅ Security confirmation for critical operations  
✅ Complete DevOps automation  
✅ Comprehensive monitoring  

## ⚙️ Project Structure

```
.
├── docker/                  # Docker configurations
│   ├── edge/               # Raspberry Pi services
│   ├── backend/            # Central services
│   └── home-assistant/     # HA templates
├── kubernetes/              # K8s manifests
│   ├── ollama/
│   ├── backend/
│   └── monitoring/
├── terraform/               # Infrastructure as Code
│   ├── ha-instance/        # HA provisioning
│   └── cluster/            # K8s setup
├── edge/                    # Raspberry Pi code
│   ├── wake-word/
│   ├── asr/
│   └── communicator/
├── backend/                 # Central services code
│   ├── user-service/
│   ├── intent-processor/
│   └── llm-gateway/
├── monitoring/              # Zabbix configs
├── scripts/                 # Automation scripts
└── docs/                    # Documentation
```

## 🚫 Limitations & Constraints

- One Raspberry Pi serves one user exclusively
- Edge devices do not control IoT devices directly
- GPU required for optimal LLM performance
- Internet connectivity required for operation

## 🆘 Support

For issues and questions:
- GitHub Issues: [Create an issue](../../issues)
- Documentation: [mikrobi_okosotthon_rendszer_srs.md](mikrobi_okosotthon_rendszer_srs.md)

## 📝 License

See [LICENSE](LICENSE) file for details.

---

**Mikrobi** - Your intelligent voice-controlled smart home assistant
