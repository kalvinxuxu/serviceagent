# Project layout

```text
backend/       FastAPI API, Agent orchestration, domain services, tools, ORM
frontend/      Next.js/React/TypeScript application and browser smoke specs
data/          Seed data plus runtime media/evidence storage
evals/         Deterministic benchmark runner, assertions, and scenarios
reports/       Versioned evaluation output and historical evidence
specs/         Feature specifications, plans, tasks, and quickstarts
runtime/       Local logs, database archives, and upload staging
bread_pics/    Source images used by media seeding
```

The following paths are runtime/API contracts and should not be moved without updating code: `data/seed`, `data/media`, `data/evidence`, `evals/scenarios`, and `reports/benchmark`. The default SQLite fallback is `runtime/db/shanye_demo.db`; the existing root `demo.db` remains for the current `.env` configuration.
