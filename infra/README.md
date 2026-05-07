# infra/

Infrastructure-as-Code for the Skate Assistant. **Story 1.1 ships the code; `terraform apply` is deferred until cloud credentials and platform-team coordination land.**

## Apply order (when ready)

1. Create the GCS state bucket out-of-band:
   ```bash
   gcloud storage buckets create gs://<project-id>-terraform-state \
     --project=<project-id> --location=<region> \
     --uniform-bucket-level-access --enable-versioning
   ```
2. Apply the main config:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init \
     -backend-config="bucket=<project-id>-terraform-state" \
     -backend-config="prefix=skate-assistant/staging"
   terraform plan
   terraform apply
   ```
3. Apply the GitHub WIF binding:
   ```bash
   cd ../github
   terraform init -backend-config="bucket=<project-id>-terraform-state" \
                  -backend-config="prefix=skate-assistant/github-wif"
   terraform apply \
     -var="project_id=<project-id>" \
     -var="github_repository=<owner>/<repo>" \
     -var="ci_service_account_email=$(cd ../terraform && terraform output -raw ci_email)"
   ```

## Modules

- `terraform/modules/network/` — VPC + private subnet + VPC connector
- `terraform/modules/secrets/` — Secret Manager + placeholder secrets (empty versions added out-of-band)
- `terraform/modules/artifact-registry/` — Docker repo for backend images
- `terraform/modules/iam/` — `cloud-run-runtime`, `ci`, `migration-job` service accounts (least-privilege)
- `terraform/modules/cloud-sql/` — PostgreSQL 16 primary (regional HA) + read replica + private IP + backup/PITR
- `github/workload-identity.tf` — GitHub OIDC → `ci` SA federation (apply after main config)

## Cross-team coordination required before apply (Story 1.1 Dev Notes)

- [ ] Confirm GCP project + billing with platform team
- [ ] Confirm SA + repo naming conventions to avoid collisions
- [ ] Confirm GitHub org / branch protection ownership
- [ ] Confirm Vercel team for the frontend integration
