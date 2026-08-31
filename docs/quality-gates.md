# Quality Gates

## V2 Validation 2026-08-24

| Gate | Result |
|---|---:|
| Backend tests | 87 passed |
| Frontend TypeScript | passed |
| SC-001～SC-009 | passed |
| Supervisor Domain Accuracy | 1.0 |
| AgentTask Schema Accuracy | 1.0 |
| Unauthorized Side-effect Count | 0 |
| V2 scenario coverage | SC-001～SC-009 |
| Query p95 | below 300 ms |

The evaluation was run against the simulated shop boundary with `LLM_PROVIDER=mock`.
