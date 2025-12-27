# Artifact Generation Summary

**Generated:** 2025-12-27 20:09:46 UTC
**Workflow Run:** [23](https://github.com/harris-boyce/boycivenga-iac/actions/runs/20543789538)

## NetBox Intent Export

Files exported from NetBox API:
```
total 152K
-rw-r--r-- 1 runner runner  34K Dec 27 20:09 prefixes.json
-rw-r--r-- 1 runner runner  27K Dec 27 20:09 prefixes.yaml
-rw-r--r-- 1 runner runner 4.1K Dec 27 20:09 sites.json
-rw-r--r-- 1 runner runner 3.8K Dec 27 20:09 sites.yaml
-rw-r--r-- 1 runner runner  908 Dec 27 20:09 tags.json
-rw-r--r-- 1 runner runner  736 Dec 27 20:09 tags.yaml
-rw-r--r-- 1 runner runner  36K Dec 27 20:09 vlans.json
-rw-r--r-- 1 runner runner  31K Dec 27 20:09 vlans.yaml
```

## Terraform tfvars

Site-specific Terraform variable files:
```
total 12K
-rw-r--r-- 1 runner runner  404 Dec 27 20:09 site-count-fleet-court.tfvars.json
-rw-r--r-- 1 runner runner 5.8K Dec 27 20:09 site-pennington.tfvars.json
```

## UniFi Configurations

Site-specific UniFi controller configurations:
```
total 8.0K
-rw-r--r-- 1 runner runner 349 Dec 27 20:09 site-count-fleet-court.json
-rw-r--r-- 1 runner runner 367 Dec 27 20:09 site-pennington.json
```

## Notes

- All artifacts are read-only exports and do not apply infrastructure changes
- Artifacts represent the current state of NetBox at generation time
- See [docs/render-pipeline.md](../docs/render-pipeline.md) for details
