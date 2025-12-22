# docs

Project documentation, architecture decisions, and operational guides.

## Contents

This directory contains comprehensive documentation for the infrastructure as code repository, including setup guides, architecture decisions, and operational procedures.

### Available Documentation

- **[render-pipeline.md](render-pipeline.md)** - Automated render pipeline for generating artifacts from NetBox
- **[netbox-schema.md](netbox-schema.md)** - NetBox schema and data models
- **[netbox-tfvars-mapping.md](netbox-tfvars-mapping.md)** - Field mapping from NetBox to Terraform variables

### Phase 3: Supply Chain Security

- **[phase3/attestation-scope.md](phase3/attestation-scope.md)** - Attestation design and scope definition for artifact provenance
- **[phase3/attestation.md](phase3/attestation.md)** - SLSA provenance attestation implementation details
- **[phase3/artifact-integrity.md](phase3/artifact-integrity.md)** - Artifact identity, naming, hashing, and integrity verification
- **[phase3/threat-model.md](phase3/threat-model.md)** - Threat model, trust boundaries, and security coverage for Phase 3
- **[phase3/terraform-boundary.md](phase3/terraform-boundary.md)** - Terraform trust boundary contract and attestation requirements

### Phase 4: Security & Operational Boundaries

- **[phase4/security.md](phase4/security.md)** - Complete security and authority boundaries documentation
- **[phase4/attestation-gate.md](phase4/attestation-gate.md)** - Reusable attestation verification gate action
- **[phase4/terraform-plan-approval-workflow.md](phase4/terraform-plan-approval-workflow.md)** - PR approval-gated Terraform plan workflow guide
- **[phase4/plan-output.md](phase4/plan-output.md)** - Terraform plan output structure and validation
- **[phase4/drift.md](phase4/drift.md)** - Infrastructure drift detection and remediation
- **[phase4/quick-start.md](phase4/quick-start.md)** - Quick start guide for contributors
- **[phase4/terraform-input-contract.md](phase4/terraform-input-contract.md)** - Terraform input contract specification
