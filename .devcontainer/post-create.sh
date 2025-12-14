#!/bin/bash
set -e

echo "Running post-create setup..."

# Initialize pre-commit if .pre-commit-config.yaml exists
if [ -f .pre-commit-config.yaml ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi

# Initialize terraform modules if any exist
if [ -d "terraform/modules" ]; then
    echo "Initializing Terraform modules..."
    for module_dir in terraform/modules/*/; do
        if [ -d "$module_dir" ] && [ -f "$module_dir/main.tf" ]; then
            echo "Initializing $module_dir..."
            (cd "$module_dir" && terraform init -backend=false) || true
        fi
    done
fi

# Initialize environment configurations
if [ -d "environments" ]; then
    echo "Terraform environments are available in environments/ directory"
fi

echo "Post-create setup complete!"
echo ""
echo "🚀 Welcome to Boycivenga IaC Development Environment!"
echo ""
echo "Quick Start:"
echo "  - Review README.md for architecture overview"
echo "  - Check CONTRIBUTING.md for development guidelines"
echo "  - Environments are in environments/ directory"
echo "  - Reusable modules are in terraform/modules/ directory"
echo ""
