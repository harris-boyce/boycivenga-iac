# Artifact Generation Summary

**Generated:** 2025-12-29 01:56:28 UTC
**Workflow Run:** [30](https://github.com/harris-boyce/boycivenga-iac/actions/runs/20562840509)

## NetBox Intent Export

Files exported from NetBox API:
```
total 156K
-rw-r--r-- 1 runner runner  34K Dec 29 01:56 prefixes.json
-rw-r--r-- 1 runner runner  27K Dec 29 01:56 prefixes.yaml
-rw-r--r-- 1 runner runner 4.1K Dec 29 01:56 sites.json
-rw-r--r-- 1 runner runner 3.8K Dec 29 01:56 sites.yaml
-rw-r--r-- 1 runner runner  908 Dec 29 01:56 tags.json
-rw-r--r-- 1 runner runner  736 Dec 29 01:56 tags.yaml
-rw-r--r-- 1 runner runner  38K Dec 29 01:56 vlans.json
-rw-r--r-- 1 runner runner  32K Dec 29 01:56 vlans.yaml
```

## Terraform tfvars

Site-specific Terraform variable files:
```
total 12K
-rw-r--r-- 1 runner runner 2.7K Dec 29 01:56 site-count-fleet-court.tfvars.json
-rw-r--r-- 1 runner runner 4.8K Dec 29 01:56 site-pennington.tfvars.json
```

## UniFi Configurations

Site-specific UniFi controller configurations:
```
total 8.0K
-rw-r--r-- 1 runner runner 349 Dec 29 01:56 site-count-fleet-court.json
-rw-r--r-- 1 runner runner 367 Dec 29 01:56 site-pennington.json
```

## Notes

- All artifacts are read-only exports and do not apply infrastructure changes
- Artifacts represent the current state of NetBox at generation time
- See [docs/render-pipeline.md](../docs/render-pipeline.md) for details
