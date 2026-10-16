# GitHub Repository Configuration & Hardening Guide

**Target Repository**: `AkashKundu114/COPPER`  
**Target Release**: `v0.1.0-alpha`  
**Date**: 2026-10-17  

---

## 1. Executive Summary

This guide provides the exact `gh` CLI commands to configure branch protection, repository metadata, labels, milestones, and security features for C.O.P.P.E.R. following the public release audit.

---

## 2. Repository Metadata & Topics

Run these commands to set an accurate description and discovery topics:

```powershell
# Set repository description
gh repo edit AkashKundu114/COPPER `
  --description "Local-first personal AI desktop assistant: offline LLMs via Ollama, persistent epistemic memory, a Guardian safety layer, and an Electron + React UI. Alpha." `
  --enable-issues=true `
  --enable-wiki=false

# Add topics
gh repo edit AkashKundu114/COPPER `
  --add-topic "local-first" `
  --add-topic "ollama" `
  --add-topic "llm" `
  --add-topic "ai-assistant" `
  --add-topic "fastapi" `
  --add-topic "react" `
  --add-topic "typescript" `
  --add-topic "privacy" `
  --add-topic "chromadb" `
  --add-topic "desktop-app" `
  --add-topic "agents"
```

---

## 3. Milestones Configuration

Establish structured release milestones:

```powershell
# Create v0.1.0-alpha milestone
gh api repos/AkashKundu114/COPPER/milestones -f title="v0.1.0-alpha" -f description="Initial public alpha release: core local chat, epistemic memory, 12 active agents, Guardian level 0-3 safety, and zero-egress offline verification." -f state="open"

# Create v0.2.0-beta milestone
gh api repos/AkashKundu114/COPPER/milestones -f title="v0.2.0-beta" -f description="Beta milestone: Tauri v2 desktop package, Tier 2 roadmap agents (Behavior, Nutrition, Evaluator), and voice duplex optimization." -f state="open"
```

---

## 4. Issue Labels Scheme

Create standard issue triage labels:

```powershell
# Severity & Type Labels
gh label create "bug" --color "d73a4a" --description "Something isn't working as documented" --force
gh label create "security" --color "b60205" --description "Security vulnerability or boundary issue" --force
gh label create "documentation" --color "0075ca" --description "Improvements or additions to documentation" --force
gh label create "enhancement" --color "a2eeef" --description "New feature or request" --force
gh label create "good first issue" --color "7057ff" --description "Good for newcomers" --force
gh label create "help wanted" --color "008672" --description "Extra attention is needed" --force
gh label create "guardian" --color "e99695" --description "Guardian safety layer or AST sandbox" --force
gh label create "memory" --color "1d76db" --description "Epistemic memory or vector store" --force
gh label create "voice" --color "f9d0c4" --description "Wake-word or TTS pipelines" --force
```

---

## 5. Branch Protection Rules

Enforce branch protection on `main` to ensure CI status checks pass before merging:

```powershell
# Require PR reviews and passing CI checks on main
gh api -X PUT repos/AkashKundu114/COPPER/branches/main/protection `
  -H "Accept: application/vnd.github+json" `
  -f required_status_checks='{"strict":true,"contexts":["backend-ci","frontend-ci"]}' `
  -f enforce_admins=false `
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' `
  -f restrictions=null
```

---

## 6. Private Vulnerability Reporting & Security

Enable automated vulnerability alerts and private vulnerability reporting:

```powershell
# Enable Dependabot alerts
gh api -X PUT repos/AkashKundu114/COPPER/vulnerability-alerts

# Enable automated security fixes
gh api -X PUT repos/AkashKundu114/COPPER/automated-security-fixes

# Enable private vulnerability reporting (allows security researchers to report privately)
gh api -X PUT repos/AkashKundu114/COPPER/private-vulnerability-reporting
```

---

## 7. CODEOWNERS

Ensure `.github/CODEOWNERS` specifies primary maintainer ownership:

```text
# Global code ownership
* @AkashKundu114

# Security critical components
/backend/app/core/guardian.py @AkashKundu114
/tests/security/ @AkashKundu114
/docs/THREAT_MODEL.md @AkashKundu114
```
