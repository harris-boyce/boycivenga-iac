# Artifact Generation Summary

**Generated:** 2025-12-27 08:37:30 UTC
**Workflow Run:** [22](https://github.com/harris-boyce/boycivenga-iac/actions/runs/20536764367)

## NetBox Intent Export

Files exported from NetBox API:
```
total 176K
-rw-r--r-- 1 runner runner  22K Dec 27 08:37 prefixes.json
-rw-r--r-- 1 runner runner  18K Dec 27 08:37 prefixes.yaml
-rw-r--r-- 1 runner runner 9.5K Dec 27 08:37 sites.json
-rw-r--r-- 1 runner runner 7.9K Dec 27 08:37 sites.yaml
-rw-r--r-- 1 runner runner  908 Dec 27 08:37 tags.json
-rw-r--r-- 1 runner runner  736 Dec 27 08:37 tags.yaml
-rw-r--r-- 1 runner runner  55K Dec 27 08:37 vlans.json
-rw-r--r-- 1 runner runner  46K Dec 27 08:37 vlans.yaml
```

## Terraform tfvars

Site-specific Terraform variable files:
```
total 24K
-rw-r--r-- 1 runner runner  380 Dec 27 08:37 site-amsterdam.tfvars.json
-rw-r--r-- 1 runner runner  404 Dec 27 08:37 site-count-fleet-court.tfvars.json
-rw-r--r-- 1 runner runner  366 Dec 27 08:37 site-los-angeles.tfvars.json
-rw-r--r-- 1 runner runner 4.5K Dec 27 08:37 site-pennington.tfvars.json
-rw-r--r-- 1 runner runner  616 Dec 27 08:37 site-sydney.tfvars.json
```

## UniFi Configurations

Site-specific UniFi controller configurations:
```
total 20K
-rw-r--r-- 1 runner runner 333 Dec 27 08:37 site-amsterdam.json
-rw-r--r-- 1 runner runner 349 Dec 27 08:37 site-count-fleet-court.json
-rw-r--r-- 1 runner runner 317 Dec 27 08:37 site-los-angeles.json
-rw-r--r-- 1 runner runner 367 Dec 27 08:37 site-pennington.json
-rw-r--r-- 1 runner runner 312 Dec 27 08:37 site-sydney.json
```

## Notes

- All artifacts are read-only exports and do not apply infrastructure changes
- Artifacts represent the current state of NetBox at generation time
- See [docs/render-pipeline.md](../docs/render-pipeline.md) for details
