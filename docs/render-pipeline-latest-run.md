# Artifact Generation Summary

**Generated:** 2025-12-27 05:07:03 UTC
**Workflow Run:** [20](https://github.com/harris-boyce/boycivenga-iac/actions/runs/20534684685)

## NetBox Intent Export

Files exported from NetBox API:
```
total 176K
-rw-r--r-- 1 runner runner  22K Dec 27 05:07 prefixes.json
-rw-r--r-- 1 runner runner  18K Dec 27 05:07 prefixes.yaml
-rw-r--r-- 1 runner runner 9.5K Dec 27 05:07 sites.json
-rw-r--r-- 1 runner runner 7.9K Dec 27 05:07 sites.yaml
-rw-r--r-- 1 runner runner  908 Dec 27 05:07 tags.json
-rw-r--r-- 1 runner runner  736 Dec 27 05:07 tags.yaml
-rw-r--r-- 1 runner runner  55K Dec 27 05:07 vlans.json
-rw-r--r-- 1 runner runner  46K Dec 27 05:07 vlans.yaml
```

## Terraform tfvars

Site-specific Terraform variable files:
```
total 20K
-rw-r--r-- 1 runner runner 1.0K Dec 27 05:07 site-amsterdam.tfvars.json
-rw-r--r-- 1 runner runner 1.6K Dec 27 05:07 site-count-fleet-court.tfvars.json
-rw-r--r-- 1 runner runner 1010 Dec 27 05:07 site-los-angeles.tfvars.json
-rw-r--r-- 1 runner runner 2.7K Dec 27 05:07 site-pennington.tfvars.json
-rw-r--r-- 1 runner runner  466 Dec 27 05:07 site-sydney.tfvars.json
```

## UniFi Configurations

Site-specific UniFi controller configurations:
```
total 20K
-rw-r--r-- 1 runner runner 333 Dec 27 05:07 site-amsterdam.json
-rw-r--r-- 1 runner runner 349 Dec 27 05:07 site-count-fleet-court.json
-rw-r--r-- 1 runner runner 317 Dec 27 05:07 site-los-angeles.json
-rw-r--r-- 1 runner runner 367 Dec 27 05:07 site-pennington.json
-rw-r--r-- 1 runner runner 312 Dec 27 05:07 site-sydney.json
```

## Notes

- All artifacts are read-only exports and do not apply infrastructure changes
- Artifacts represent the current state of NetBox at generation time
- See [docs/render-pipeline.md](../docs/render-pipeline.md) for details
