---
name: generateservicemap
description: >
  Deep agentic crawl of a code repository to produce a machine-readable servicemap.json that maps every service,
  app, library, data store, external dependency, infrastructure resource, CI/CD pipeline, and inter-service
  communication path — including authentication, authorization, public/private endpoints, and confidence scores.
  Use this skill whenever the user says /generateservicemap, asks to "map a repo", "build a service map",
  "generate a service topology", "trace service dependencies", "map infrastructure", or any variation of
  "understand how this codebase fits together." Also trigger when the user asks to update or enrich an
  existing servicemap.json. This skill is designed for DEEP crawls — it does not support shallow or partial
  mapping. The output is JSON optimized for machine consumption by other Claude skills and agents, not for
  direct human reading.
---

# /generateservicemap

Generate a comprehensive, machine-readable `servicemap.json` from a repository by performing a deep, phased
agentic crawl. The map captures services, apps, libraries, infrastructure, data stores, external dependencies,
inter-service communication, security posture, observability surface, and ownership — with confidence scores
on every discovery.

## Invocation

```
/generateservicemap --path <output-path>
```

- `--path` (optional): Where to write the output file. Defaults to `./servicemap.json` in the current
  working directory. Use a specific path to control where the map lands (e.g.,
  `/generateservicemap --path tools/servicemap.json`).

## Before You Start

1. **Locate the schema**: Look for `references/schema.md` relative to the directory where `servicemap.json`
   will be written (i.e., sibling `references/` folder next to the output path). For example:
   - Output path `tools/servicemap.json` → read `references/schema.md`
   - Output path `./servicemap.json` → read `./references/schema.md`

   Read the schema to internalize the full JSON structure. Every field matters — the schema is
   the contract that downstream skills and apps depend on.
2. Check if a `servicemap.json` already exists at the target path. If it does, this is an **incremental
   update** — read the Incremental Update Strategy section below.

## Crawl Philosophy

This is a DEEP crawl. The goal is to trace every meaningful connection, not to produce a quick summary.
The reason depth matters is that this map will be consumed by other Claude instances and automated tooling
that need to reason about blast radius, security boundaries, deployment dependencies, and operational
risk. A shallow map that misses a database connection or an unauthenticated endpoint is worse than no map,
because it creates false confidence.

That said, depth must be managed against context constraints. The phased approach below is how you do that.

## Phase 1: Discovery — Identify All Components

**Goal**: Build a manifest of every discrete component in the repo without deep-diving any of them yet.

Scan the repository structure to identify:

- **Services**: Anything that runs independently. Heuristics: has its own Dockerfile, has a `package.json`
  / `go.mod` / `Cargo.toml` / `pyproject.toml` / `build.gradle` / `pom.xml` with an entrypoint, has its
  own Terraform module that provisions compute (ECS, Lambda, EC2, Cloud Run, etc.), or has its own
  Kubernetes Deployment manifest.
- **Apps**: Frontend applications, mobile apps, CLI tools. Distinguished from services by being
  user-facing rather than API-facing.
- **Libraries**: Shared internal packages without their own entrypoint. Look for workspace members,
  internal package references, monorepo package directories.
- **Infrastructure**: Terraform/OpenTofu/Pulumi/CloudFormation directories. Each module or stack is a
  component.
- **CI/CD Pipelines**: GitHub Actions workflows, GitLab CI, CircleCI, Jenkins, etc.
- **Data stores**: Database migration directories, schema files, seed data.

For each component discovered, record:
- `name`, `type`, `path` (relative to repo root), `language`, `framework`, `platform`
- `confidence`: How certain you are this is correctly classified (0.0–1.0)
- `discovery_method`: What heuristic identified it (e.g., "Dockerfile present", "Kubernetes Deployment manifest")

Write the Phase 1 manifest to memory before proceeding. This is your roadmap for subsequent phases.

## Phase 2: Deep Dive — Analyze Each Component

**Goal**: For each component from Phase 1, extract detailed metadata.

Work through components one at a time (or in small batches if they're lightweight). For each:

### Services and Apps

- **Endpoints**: Trace route definitions. Look for Express/Koa/Hono routes, FastAPI/Flask/Django URL
  patterns, Spring `@RequestMapping`, Go chi/mux/gin routes, Rails routes.rb, etc.
  - For each endpoint: method, path, whether it's public or private (behind auth middleware),
    authentication mechanism (JWT, API key, OAuth, session, mTLS, none), authorization requirements
    (roles, scopes, policies).
- **Dependencies — other services**: Trace HTTP client calls, gRPC stubs, SDK imports that point to
  other internal services. Look for base URLs, service names in env vars, Kubernetes service DNS names.
- **Dependencies — data stores**: Database connection strings/configs, ORM model definitions, cache
  client instantiation, S3/blob storage client usage, message queue producer/consumer setup.
- **Dependencies — external APIs**: Third-party SDK imports and API calls (Stripe, Twilio, SendGrid,
  Auth0, Datadog, PagerDuty, etc.).
- **Environment and config**: How config is loaded — env vars, config files, Vault references, AWS
  Secrets Manager, Kubernetes ConfigMaps/Secrets. Catalog every env var referenced.
- **Observability**: Health check endpoints, logging framework, tracing instrumentation (OpenTelemetry,
  Datadog APM, Jaeger, Zipkin), metrics endpoints, alerting rules.
- **Container config**: Dockerfile analysis — base image, exposed ports, build stages, runtime user.
  Docker Compose service definitions if present.

### Infrastructure

- **Terraform / IaC**: For each module, catalog:
  - Resources provisioned (with types: `aws_ecs_service`, `aws_rds_instance`, etc.)
  - Variables and their defaults
  - Outputs (these are the interface other modules/services consume)
  - Remote state references (how modules connect to each other)
  - Provider and backend configuration
  - Workspaces or environment parameterization
- **Kubernetes manifests**: Deployments, Services, Ingresses, NetworkPolicies, HPA, PDB, ServiceAccounts,
  RBAC roles. Map port relationships between Deployment containers and Service/Ingress definitions.

### CI/CD Pipelines

- Trigger conditions (push, PR, schedule, manual)
- Steps and their purposes
- Which services/apps they build, test, and deploy
- Environment targets (dev, staging, prod)
- Secret references
- Deployment strategy (rolling, blue-green, canary)

### Libraries

- What exports they provide
- Which services/apps import them
- Version pinning strategy

## Phase 3: Trace Connections

**Goal**: Build the relationship graph between all components.

This phase is where the map becomes genuinely valuable. Using the data from Phase 2:

1. **Service-to-service**: Match outbound HTTP/gRPC/queue calls in one service to inbound endpoint
   definitions in another. Record the protocol, whether it's sync or async, and the specific
   endpoints involved.
2. **Service-to-data-store**: Match database connection configs to Terraform/IaC resources that
   provision those stores. Flag shared databases (multiple services connecting to the same store).
3. **Service-to-external**: Catalog all third-party API dependencies.
4. **Infrastructure-to-service**: Map Terraform resources to the services they support (e.g.,
   `aws_ecs_service` → the service that runs on it).
5. **Pipeline-to-service**: Map CI/CD workflows to the services they deploy.
6. **Library-to-consumer**: Map internal library usage across all services.

For each connection:
- `source`, `target`, `type` (http, grpc, graphql, queue, database, library, infrastructure)
- `async`: boolean
- `protocol_details`: method, path, queue name, topic, etc.
- `auth_required`: what auth the connection uses
- `confidence`: how certain you are this connection exists

## Phase 4: Assemble and Validate

**Goal**: Produce the final `servicemap.json`.

1. Assemble all phase outputs into the schema defined in `references/schema.md`.
2. **Validate completeness**: Every service discovered in Phase 1 should have a deep-dive entry from
   Phase 2 and connections from Phase 3. If any are missing, go back and fill them.
3. **Identify stubs**: Any service, data store, or dependency referenced but NOT found in this repo
   gets a stub entry with `"stub": true` and a `"stub_reason"` explaining what's missing. These are
   the TODOs for multi-repo mapping.
4. **Set timestamps**: `last_crawled` on every component and `generated_at` on the root.
5. Write to the `--path` location.

## Incremental Update Strategy

When an existing `servicemap.json` is found at the target path:

1. Read and parse the existing map.
2. Check `schema_version` compatibility. If the major version differs, warn the user and offer to
   regenerate from scratch.
3. Crawl the repo as normal (all four phases).
4. Merge strategy: **crawl wins for discovered data, preserve manual annotations.**
   - Any field with `"manual_override": true` is preserved from the existing map, not overwritten.
   - New components discovered in the crawl are added.
   - Components in the existing map but not found in the crawl get flagged with
     `"stale": true` and `"stale_since": "<timestamp>"` rather than removed.
   - Connections are fully rebuilt from the crawl (they're too complex to merge partially).
   - Stubs from other repos are preserved unchanged.
5. Update all `last_crawled` timestamps for components that were re-crawled.

## Confidence Scoring Guide

Every discovery should include a confidence score. Use this calibration:

- **1.0**: Definitive evidence. A Dockerfile with an ENTRYPOINT, a Kubernetes Deployment manifest, an
  explicit route definition.
- **0.8–0.9**: Strong evidence. A database connection string in config pointing to a named resource,
  an import of another internal package.
- **0.5–0.7**: Inferential. An env var that looks like a service URL but isn't confirmed, a comment
  referencing another service, a TODO mentioning a dependency.
- **0.3–0.4**: Speculative. Naming conventions suggest a relationship, a file structure implies a
  service but no entrypoint found.
- **< 0.3**: Weak signal. Include only if it fills a gap that would otherwise be a stub.

## Output

The output is a single JSON file conforming to the schema in `references/schema.md`. The JSON should
be pretty-printed with 2-space indentation for version control friendliness, even though it's
machine-targeted.

After writing the file, report to the user:
- Total components discovered (by type)
- Total connections traced
- Number of stubs (TODOs for other repos)
- Any components with average confidence below 0.5 (these need human review)
- If incremental: what changed since last crawl

## Context Management

Large repos will challenge context limits. Strategies:

- In Phase 1, use directory listings and file existence checks rather than reading file contents.
  You're just building the manifest.
- In Phase 2, process one component at a time. Read only the files relevant to that component,
  extract what you need, then move on. Don't try to hold the entire repo in context.
- In Phase 3, work from the structured data you already extracted in Phase 2, not from raw files.
  You should rarely need to re-read source files in this phase.
- If the repo is exceptionally large (50+ services), consider batching Phase 2 into groups of
  5–10 services, writing intermediate results to a temp file between batches.
