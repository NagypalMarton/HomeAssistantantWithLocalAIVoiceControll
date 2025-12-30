.PHONY: help setup-local start stop restart logs clean deploy-dev deploy-prod test lint

# Default target
help:
	@echo "Home Assistant + Ollama LLM DevOps Project"
	@echo ""
	@echo "Available targets:"
	@echo "  setup-local    - Setup local development environment"
	@echo "  start          - Start local services with Docker Compose"
	@echo "  stop           - Stop local services"
	@echo "  restart        - Restart local services"
	@echo "  logs           - View logs from all services"
	@echo "  clean          - Clean up Docker volumes and containers"
	@echo ""
	@echo "  deploy-dev     - Deploy to development Kubernetes"
	@echo "  deploy-prod    - Deploy to production Kubernetes"
	@echo "  tf-init        - Initialize Terraform"
	@echo "  tf-plan        - Plan Terraform changes"
	@echo "  tf-apply       - Apply Terraform changes"
	@echo ""
	@echo "  test           - Run tests"
	@echo "  lint           - Lint code and configurations"
	@echo "  security-scan  - Run security scans"
	@echo ""
	@echo "  user-create    - Create new user (make user-create USER=username)"
	@echo "  user-delete    - Delete user (make user-delete USER=username)"

# Local Development
setup-local:
	@echo "Setting up local environment..."
	chmod +x scripts/*.sh
	chmod +x monitoring/zabbix/scripts/*.sh
	./scripts/setup-local.sh

start:
	@echo "Starting services..."
	cd docker && docker-compose up -d

stop:
	@echo "Stopping services..."
	cd docker && docker-compose down

restart: stop start

logs:
	cd docker && docker-compose logs -f

clean:
	@echo "Cleaning up..."
	cd docker && docker-compose down -v
	docker system prune -f

# Kubernetes Deployment
deploy-dev:
	@echo "Deploying to development..."
	./scripts/deploy-k8s.sh dev

deploy-prod:
	@echo "Deploying to production..."
	./scripts/deploy-k8s.sh prod

# Terraform
tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan -var-file="environments/dev/terraform.tfvars"

tf-apply:
	cd terraform && terraform apply -var-file="environments/dev/terraform.tfvars"

tf-destroy:
	cd terraform && terraform destroy -var-file="environments/dev/terraform.tfvars"

# Testing
test:
	@echo "Running tests..."
	docker-compose -f docker/docker-compose.yml config
	helm lint helm/ha-llm-stack
	cd terraform && terraform fmt -check -recursive

lint:
	@echo "Linting configurations..."
	yamllint kubernetes/ helm/ .github/
	helm lint helm/ha-llm-stack

security-scan:
	@echo "Running security scan..."
	trivy fs --security-checks vuln,config .

# User Management
user-create:
	@if [ -z "$(USER)" ]; then \
		echo "Error: USER variable required. Usage: make user-create USER=username"; \
		exit 1; \
	fi
	./scripts/user-provision.sh $(USER)

user-delete:
	@if [ -z "$(USER)" ]; then \
		echo "Error: USER variable required. Usage: make user-delete USER=username"; \
		exit 1; \
	fi
	kubectl delete namespace ha-llm-user-$(USER)
	helm uninstall ha-llm-$(USER) -n ha-llm-user-$(USER) || true

# Monitoring
monitoring-start:
	cd monitoring/zabbix && docker-compose up -d

monitoring-stop:
	cd monitoring/zabbix && docker-compose down

# Build
build-images:
	@echo "Building Docker images..."
	docker build -t ha-llm/home-assistant:latest docker/home-assistant/
	docker build -t ha-llm/ollama:latest docker/ollama/

push-images:
	@echo "Pushing Docker images..."
	docker push ha-llm/home-assistant:latest
	docker push ha-llm/ollama:latest

# Helm
helm-package:
	helm package helm/ha-llm-stack

helm-install:
	helm install ha-llm-stack ./helm/ha-llm-stack \
		--namespace ha-llm-system \
		--create-namespace

helm-upgrade:
	helm upgrade ha-llm-stack ./helm/ha-llm-stack \
		--namespace ha-llm-system

helm-uninstall:
	helm uninstall ha-llm-stack -n ha-llm-system

# Utilities
kubectl-context:
	kubectl config current-context
	kubectl cluster-info

check-gpu:
	kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'

check-resources:
	kubectl top nodes
	kubectl top pods -n ha-llm-system

ollama-models:
	@echo "Available Ollama models in cluster:"
	kubectl exec -n ha-llm-system deployment/ollama -- ollama list

backup:
	@echo "Creating backup..."
	mkdir -p backups
	kubectl get all -n ha-llm-system -o yaml > backups/backup-$(shell date +%Y%m%d-%H%M%S).yaml
	helm get values ha-llm-stack -n ha-llm-system > backups/values-$(shell date +%Y%m%d-%H%M%S).yaml
