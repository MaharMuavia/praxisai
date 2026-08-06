# Changelog

All notable release changes are recorded here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) structure. A semantic
versioning policy has not yet been adopted.

## Unreleased

### Added

- Release governance, contribution, security-reporting, and decision-record templates.
- Consolidated XPRIZE release branch based on the complete implementation stack.
- Production security headers for the web and API layers.
- Split CI contracts for fast checks, database/API tests, security, builds, and E2E.
- Dependency, full-history secret, SBOM/provenance, and container-image release gates.

### Changed

- Release verification now treats generated browser output, temporary documents,
  caches, and logs as untracked artifacts.
- Web runtime upgraded to Next.js 16 and Node.js 22.23.2 LTS; API security-sensitive
  dependencies upgraded to current fixed releases.
- Container bases moved from Debian 12 to Debian 13 and Docker build contexts are
  explicitly restricted.

### Removed

- Tracked local Playwright screenshots and a generated demo credential PDF.

## 0.1.0 - Unreleased

- Initial production-oriented PraxisAI modular monolith baseline.
