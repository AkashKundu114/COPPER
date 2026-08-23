# C.O.P.P.E.R. CI/CD Pipeline

This directory contains the full GitHub Actions pipeline for C.O.P.P.E.R. It is
designed to mirror a production engineering org's release process: every
change is linted, type-checked, tested, benchmarked, security-scanned, and
containerized before it can reach `main`, and deployments to staging/production
go through protected GitHub Environments with manual approval gates.

## Workflow Inventory

| Workflow | File | Trigger | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend CI** | `backend-ci.yml` | push/PR to `backend/**`, `tests/**` | Ruff lint + format, mypy, pytest matrix (3.11/3.12) with Postgres+Redis services, coverage upload, routing/guardian benchmark regression gate, Bandit + pip-audit security scan |
| **Frontend CI** | `frontend-ci.yml` | push/PR to `frontend/**` | oxlint, `tsc` project build, Vite build matrix (Node 18/20), bundle size report, `npm audit` |
| **Docker Build & Publish** | `docker-build.yml` | push to `main`/tags, PRs touching backend/frontend/infra | Multi-arch (amd64/arm64) image builds pushed to GHCR with semantic tags, Trivy image scanning, Compose config validation |
| **CodeQL Advanced Security Analysis** | `codeql.yml` | push, PR, weekly schedule | Static analysis (security-extended + security-and-quality query packs) for Python and JS/TS |
| **Security Scan** | `security-scan.yml` | push, PR, nightly | Gitleaks secret scanning, GitHub dependency review, Trivy filesystem scan, Hadolint Dockerfile linting |
| **Release** | `release.yml` | push of `v*.*.*` tag | Builds frontend/backend artifacts, generates a changelog from commit history, publishes a GitHub Release |
| **PR Checks** | `pr-checks.yml` | PR opened/edited/synchronized | Enforces Conventional Commit PR titles, auto-labels by size and by changed path |
| **Deploy** | `deploy.yml` | successful Docker build on `main`, or manual dispatch | Rolls out to the `staging` GitHub Environment automatically; `production` requires a manual dispatch approved via environment protection rules |
| **Nightly Build & Extended Tests** | `nightly.yml` | daily schedule | Cross-OS (Ubuntu/Windows/macOS) and cross-Python test matrix, frontend cross-platform build, stale issue/PR housekeeping |

## Quality Gates

A PR cannot merge into `main` unless:
1. `Backend CI` and `Frontend CI` summary jobs are green (lint, types, full test suite).
2. The **routing/guardian benchmark gate** stays at or above 97% / 99% accuracy — this
   is a hard regression check on the agent router and safety engine, not just a
   smoke test.
3. `Security Scan` and `CodeQL` come back clean of new high/critical findings.
4. The PR title follows Conventional Commits (enforced by `pr-checks.yml`).

Configure these as **required status checks** under
**Settings → Branches → Branch protection rules** for `main`.

## Environments & Secrets

`deploy.yml` targets two GitHub Environments, each with its own protection rules
(recommended: required reviewers on `production`):

| Environment | Secret | Notes |
| :--- | :--- | :--- |
| `staging` | `STAGING_KUBECONFIG` (base64-encoded kubeconfig) | Auto-deploys after a successful `main` image build |
| `production` | `PRODUCTION_KUBECONFIG` (base64-encoded kubeconfig) | Manual `workflow_dispatch` only |

If a `KUBECONFIG` secret isn't configured, the job falls back to
`kubectl apply --dry-run=client` so the pipeline still runs green in forks and
demo environments without a live cluster.

Other optional secrets:
- `CODECOV_TOKEN` — backend coverage upload
- `GITHUB_TOKEN` — provided automatically by Actions; used for GHCR push, labeling, and dependency review

## Dependency Management

`dependabot.yml` opens weekly PRs for `pip` (backend), `npm` (frontend),
`docker` (base images), and `github-actions` (this pipeline itself), grouped
by minor/patch to keep the PR volume manageable.
