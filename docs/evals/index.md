# Pre-flight Evals

Three guardrails that intercept high-risk modifications before any code is written. Each eval is referenced in the CLAUDE.md pre-flight table — the table maps file types to the eval that fires before changes to that file type.

HALT instructions in any eval must not be overridden by task urgency, confidence, or prior approval of similar changes.

---

* [Eval: Environment](eval-environment.md) — Pre-flight check intercepting modifications to shared production resources: ci.yml, CLAUDE.md, docs/skills/, and docs/ADR/.
* [Eval: Operation Scope](eval-operation-scope.md) — Pre-flight check intercepting modifications to app/main.py and tests/, ensuring changes stay within the intended scope of the current task.
* [Eval: Contract Pre-flight](eval-contract-preflight.md) — Pre-flight check intercepting modifications to WireMock stubs and Pact files to prevent contract drift between consumer and provider.
