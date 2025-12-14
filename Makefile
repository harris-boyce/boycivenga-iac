.PHONY: help init fmt validate lint security plan apply clean docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Initialize Terraform in all environments
	@echo "Initializing Terraform..."
	@cd environments/site-primary && terraform init
	@cd environments/site-secondary && terraform init
	@echo "✓ Initialization complete"

fmt: ## Format all Terraform files
	@echo "Formatting Terraform files..."
	@terraform fmt -recursive
	@echo "✓ Formatting complete"

validate: ## Validate Terraform configurations
	@echo "Validating Terraform configurations..."
	@cd environments/site-primary && terraform validate
	@cd environments/site-secondary && terraform validate
	@echo "✓ Validation complete"

lint: ## Run linters (tflint)
	@echo "Running tflint..."
	@tflint --init
	@tflint --recursive --config .tflint.hcl
	@echo "✓ Linting complete"

security: ## Run security scans (tfsec, checkov)
	@echo "Running security scans..."
	@echo "→ tfsec"
	@tfsec . --minimum-severity MEDIUM
	@echo "→ checkov"
	@checkov -d . --framework terraform --quiet
	@echo "✓ Security scans complete"

plan-primary: ## Plan changes for primary site
	@echo "Planning changes for site-primary..."
	@cd environments/site-primary && terraform plan

plan-secondary: ## Plan changes for secondary site
	@echo "Planning changes for site-secondary..."
	@cd environments/site-secondary && terraform plan

apply-primary: ## Apply changes for primary site
	@echo "Applying changes for site-primary..."
	@cd environments/site-primary && terraform apply

apply-secondary: ## Apply changes for secondary site
	@echo "Applying changes for site-secondary..."
	@cd environments/site-secondary && terraform apply

clean: ## Clean Terraform files
	@echo "Cleaning Terraform files..."
	@find . -type d -name ".terraform" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "terraform.tfstate.backup" -delete 2>/dev/null || true
	@find . -type f -name ".terraform.lock.hcl" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete"

docs: ## Generate module documentation
	@echo "Generating module documentation..."
	@terraform-docs markdown table --output-file README.md --output-mode inject terraform/modules/ubiquiti
	@terraform-docs markdown table --output-file README.md --output-mode inject terraform/modules/homebridge
	@terraform-docs markdown table --output-file README.md --output-mode inject terraform/modules/automation
	@echo "✓ Documentation generated"

pre-commit: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@pre-commit install
	@echo "✓ Pre-commit hooks installed"

pre-commit-run: ## Run pre-commit hooks on all files
	@echo "Running pre-commit hooks..."
	@pre-commit run --all-files

test: fmt validate lint security ## Run all tests (format, validate, lint, security)
	@echo "✓ All tests passed"

ci: test ## Run CI checks locally
	@echo "✓ CI checks complete"
