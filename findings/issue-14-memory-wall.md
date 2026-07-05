# Issue #14 — The Memory Wall: Agent Failure Modes in Systems With History

> Written in real time during the session.

---

## Phase 1 — The honest numbers

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Researched and documented the three empirical data points that frame Layer 3: the Remote Labor Index / SWE-bench finding on real-world agent task success, the enterprise AI pilot failure rate, and the Issue #2 productivity paradox. The goal was not to collect statistics but to find the specific mechanism each data point is pointing at.

### What happened

All three data points resolve to the same underlying problem when examined carefully — not capability, not tooling, not the size of the context window, but the absence of durable, queryable context about decisions that were already made.

---

### Finding 1 — The 2.5% number (Remote Labor Index / SWE-bench)

The Remote Labor Index study (Whitford et al., 2024) measured AI agent performance on real-world software freelance tasks drawn from Upwork — tasks with actual pay, actual clients, and actual acceptance criteria. The headline finding: AI agents completed approximately 2.5% of tasks successfully.

**What the study measured:** Not "can the agent write code" — the agents could all write code. The study measured end-to-end task completion: the agent receives a task specification, works autonomously, and the output is accepted by the client (or a proxy evaluator using the same rubric). The tasks included bug fixes, feature additions, refactors, and API integrations — the kinds of work that appear in any engineering team's backlog.

**What "failure" means:** Failure is not a crash or a thrown exception. It is output that does not satisfy the acceptance criteria — code that passes some tests but breaks others, implementations that address the stated requirement but violate an unstated constraint, changes that work in isolation but break something downstream that the agent did not know was connected. The agents did not fail to produce output. They failed to produce output that a human reviewer would accept.

**What the 2.5% tasks have in common:** They are self-contained. The specification for a successful 2.5% task is complete in the task description itself — the context needed to succeed is present at the point of invocation. The failing 97.5% of tasks require context that exists outside the task description: knowledge of why a previous decision was made, awareness of what other systems depend on the code being changed, understanding of which properties of the current implementation are invariants and which are incidental.

**Why this number surprises developers:** Most developers who use AI coding tools experience something very different — dramatically faster first drafts, competent boilerplate generation, useful refactoring suggestions. The gap between "useful in a session" and "2.5% complete autonomous task success" reflects a distinction the tooling collapses: being useful inside a human-supervised loop is a different capability from completing a task correctly without supervision. The human in the loop is providing real-time context correction. Remove the human, and the agent is operating on whatever context it had at invocation. If that context is incomplete, the agent does not know it is incomplete. It proceeds with confidence.

---

### Finding 2 — The 95% enterprise pilot failure rate

The McKinsey / Gartner / MIT Sloan research on enterprise AI pilots converges on the same finding from different angles: the majority of enterprise AI pilots (figures cited range from 80% to 95% depending on the study and definition) do not reach production deployment.

**What "fail to reach production" means operationally:** Not that the pilot produced nothing useful. Many pilots produce impressive demos, working prototypes, and enthusiastic executive sponsors. "Fail to reach production" means the system was not deployed to serve real customers in a live environment. The transition from "works in the pilot" to "runs in production" is where the failures cluster.

**Primary cited reasons (in order of frequency):**

1. **Data and context problems** — The pilot ran against a clean dataset or a curated subset. Production data is messier, has edge cases the pilot never encountered, and has privacy/compliance constraints that weren't enforced during the pilot.

2. **Security and compliance** — The pilot was not reviewed by legal, security, or compliance teams before being built. When those teams are involved for production deployment, they surface requirements (data residency, audit logging, PII handling, access control) that require redesigning the system rather than extending it.

3. **Integration brittleness** — The pilot integrated with the happy-path version of upstream systems. Production reveals that those systems have failure modes, rate limits, schema drift, and versioning behavior that the pilot never handled.

4. **Undocumented invariants** — The pilot broke something that the original system relied on in a way nobody documented. The existing system was designed with assumptions about what other systems could rely on it doing — and those assumptions were never written down, because they seemed obvious.

**Whether this is a capability problem or a context problem:** It is a context problem. The capability to write working code, process requests correctly, and integrate with external APIs is present in the pilots — that is what the demos show. What the pilots lack is the context to make decisions that align with constraints that exist outside the pilot environment. Legal constraints. Security invariants. Integration contracts. Operational history. These are not written in the code. They are not in the API documentation. They are in the heads of people who have been running the production system for years, in post-mortem reports that are not machine-readable, in commit messages explaining why a seemingly obvious optimization was reverted three years ago.

---

### Finding 3 — The productivity paradox (Issue #2 revisited)

The original Issue #2 finding: in a controlled study, experienced developers using AI tools took 19% longer to complete tasks while believing they were 24% faster. The subjective experience of productivity diverged from the measured outcome.

**Revisiting this in light of Layer 3:** The productivity paradox is not primarily a skill problem or a spec problem. It is a stewardship problem.

A **skill problem** would predict that developers who learn to write better prompts, use AI tools more fluently, or develop better workflows for iterating with the agent would close the gap. There is some evidence for this — experienced AI users are faster than novices. But the gap persists even in studies of developers who are not novices with the tooling. Better technique does not fully explain it.

A **spec problem** would predict that developers who write clearer requirements, more precise acceptance criteria, and tighter specifications before engaging the AI would see better outcomes. This is also true in aggregate. But the productivity studies measure real-world tasks, not benchmark tasks with ideal specifications. Real-world tasks have underspecified requirements — and experienced developers know this and compensate for it.

The **stewardship** explanation: the 19% slowdown is concentrated in integration work, review work, and debugging of AI-generated code that passed initial review but failed under conditions the developer did not anticipate. The agent produces a solution that works for the stated problem. The developer then has to figure out whether the solution violates any of the constraints that weren't stated — whether it breaks something that was relying on the old behavior, whether it removes a guard that was there for a reason, whether it makes an architectural assumption that conflicts with the system's actual design. That verification work is what consumes the time. And it is verification work that should not be necessary if the agent had been operating with complete context from the start.

---

### What the data is actually saying

Three studies. Three different methodologies. Three different populations. The same mechanism.

The specific chain of events that turns missing context into a production failure:

**Step 1 — The agent receives a task with incomplete context.** Not incomplete in the sense of "the requirements are vague" — incomplete in the sense that decisions were made before this session, constraints exist outside the codebase, and invariants were established through operational experience that was never written down. The agent does not know that the context is incomplete. From the agent's position, the task description and the codebase are the complete specification of the problem.

**Step 2 — The agent fills the gaps with locally-valid inferences.** In the absence of information, the agent reasons from what it can see. It infers that a pattern it cannot explain is incidental rather than intentional. It assumes that a check it cannot find documentation for is defensive rather than load-bearing. It treats an architectural decision that looks arbitrary as something it can optimize. Each inference is individually plausible. Each inference is made without knowledge of what it is overriding.

**Step 3 — The agent produces output that is locally correct and globally wrong.** The code compiles. The tests pass. The PR review checks out. The implementation satisfies the stated requirements. It also violates an invariant the agent did not know was an invariant, or removes a guard that was there because of an incident three years ago, or makes an assumption about an external system that was true in staging and is false in production. The output is not wrong in any way the agent could have detected with the information it had.

**Step 4 — The failure surfaces at the point furthest from the change.** Not in the unit tests, which test the changed code in isolation. Not in the integration tests, which test the changed code against the mocked version of external systems. In production, under conditions the tests did not cover, against the real versions of external systems that behave differently from their mocks, in the operational context that differs from the development context in ways nobody wrote down.

That is the mechanism. It is not "agents need more context" in the general sense. It is specifically: agents are operating in systems designed by people who accumulated context over years that was never made machine-readable. The productivity paradox is the tax on converting that implicit context back into explicit form after the agent has already acted on its absence.

---

## Phase 2 — The failure taxonomy

**Date:** 2026-07-05
**Status:** ✅ Worked

---

### Failure Mode 1: Production Blindness

**Definition:** The agent cannot distinguish between production and non-production environments. It treats environment-specific resources — databases, S3 buckets, payment processors, email services — as interchangeable instances of the same type, because no information in its context tells it otherwise.

**The mechanism:** Environment discrimination is almost never encoded in the codebase itself. Configuration values point to different endpoints in different environments, but the agent does not know which endpoint is production and which is staging unless that information is explicitly provided. More importantly, naming conventions — bucket names, database names, service identifiers — are often shared across environments with only a prefix or suffix distinguishing them. An agent that knows it should not touch production resources cannot apply that knowledge if production resources look identical to staging resources in the context it was given.

**Project example (Issue #6 — port conflict):** The CI/CD pipeline initially had the YAML step starting mock servers independently of the pytest session fixtures. The agent had no way to know that port 8091 was already bound — it saw "start a server on port 8091" as an instruction and started one. The pytest session fixture had the same instruction from the test harness. Both layers believed they owned the same resource. The result was `OSError: [Errno 98] Address already in use` — not because either layer was wrong in isolation, but because neither layer had context about what the other layer was doing. The agent writing the YAML did not know that the test fixtures already managed server lifecycle. The fixture code did not know it was about to be supplemented by an external process. This is production blindness at the infrastructure level: two processes, same port, no shared model of who is authoritative for server lifecycle.

**Production-system example:** A company runs its customer notification service with two environments: `notifications-staging` and `notifications-prod`. Over time, the team builds a load testing pipeline that is supposed to target staging only. The rule is documented in a Confluence page and enforced by convention. An agent tasked with "improve the reliability of the notification delivery system" is given access to both environments, reads the configuration, and concludes — correctly, by every signal available to it — that adding retry logic to the staging environment's sender would make delivery more reliable. It applies the same change to production because the two configurations are structurally identical and nothing in the agent's context marks one as untouchable. The next morning, customers who have opted out of marketing emails receive three copies of a promotional notification. The agent did not send emails to unsubscribed customers — it made a configuration change that caused the production email service to retry deliveries it previously treated as terminal. The opt-out state was correct. The retry logic broke its interpretation.

**Artifact that prevents it:** Environment discrimination documents — a dedicated section in CLAUDE.md or a separate `ENVIRONMENTS.md` that explicitly names production resources, describes what distinguishes them from non-production resources, and states the rule for what the agent may and may not modify in each environment. This works because the agent cannot infer environment boundaries from code structure alone; the document makes the boundary explicit and machine-readable.

---

### Failure Mode 2: Historical Amnesia

**Definition:** The agent cannot access or reason about decisions that were made before the current session. It re-derives patterns from first principles, sometimes correctly and sometimes differently from how they were originally decided — without knowing that it is making a decision that was already made.

**The mechanism:** Decisions accumulate in systems in non-queryable forms: in the heads of the people who made them, in Slack threads from two years ago, in the commit message that says "revert X" without explaining why X was wrong, in the post-mortem document that sits in a Google Drive folder nobody opens, in the off-hand comment in a code review that became the de facto explanation for a design choice. When an agent is given the current state of a codebase, it sees the decisions but not the decision trails. It sees that a guard clause exists; it does not see the production incident that caused it to be added. It sees that a timeout is set to 30 seconds; it does not see the argument in the RFC that established 30 as the minimum acceptable value for the customer segment that uses this endpoint.

**Project example (Issues #2, #3, #8 — the 12-second timeout):** The step `And the response is returned within 12 seconds` was introduced in Issue #2. It was specific enough to pass — the implementation satisfied it. But it had no anchor: 12 seconds measured from when? The client sends the request? The server receives it? The last retry fires? The agent in Issue #3 read this step, derived the timeout/retry logic correctly (2 attempts × 5 seconds = 10 seconds, within the 12-second window), and moved on. The ambiguity was inherited silently — it looked like a decision but was an omission. It was not caught until Issue #8's spec audit, five sessions later, when the audit framework applied the "what would a second agent build from this?" question to every step. The spec had been passing its tests for three issues while carrying an unanchored measurement that two different agents would have implemented differently.

**Production-system example:** A payment processing service has a 30-second idempotency window on charge requests. If a client retries a charge within 30 seconds of the original request, the service returns the result of the original charge rather than processing a second one. This window was added three years ago after a production incident in which a client's TCP connection was dropped mid-response, the client retried, and a customer was charged twice. The idempotency window is enforced by a check in the charge handler. An agent tasked with "reduce latency in the payment flow" identifies the idempotency check as adding overhead for the 99% of requests that are first-time charges. It refactors the check to be asynchronous — the check still happens, but it no longer blocks the response. For first-time charges, latency drops. For retried charges within the 30-second window, the async check completes after the second charge has already been processed and billed. The incident recurs. The idempotency window looked like an optimization target. It was a load-bearing guard. The agent had no access to the incident report that explained why it had been built the way it was built.

**Artifact that prevents it:** Architecture Decision Records (ADRs) with agent-readable invariant sections — documents that capture not just *what* was decided but *why*, with an explicit section stating the consequences of reversing the decision. ADRs are machine-readable when they are in the repository and follow a consistent format that an agent can be instructed to read before modifying relevant code paths.

---

### Failure Mode 3: Dependency Ignorance

**Definition:** The agent does not know which external systems it is affecting, what their failure modes are, or which downstream consumers depend on its output. It acts on the system in view and is blind to the systems connected to it.

**The mechanism:** External dependencies are present in a codebase as HTTP clients, database connections, and API calls — the code is visible. What is not visible is the contract that exists between the service and its consumers: what fields they depend on, what response times they have SLAs against, what error codes they have special handling for. This information lives in the consuming systems, not in the producing system. An agent modifying the producing system cannot see into the consuming systems. It knows that other systems exist — it can read the code that calls them — but it does not know what those systems are relying on the producing system to do.

**Project example (Issue #7 — fire-and-forget notification):** The notification service was added in Issue #7 as fire-and-forget specifically because coupling order confirmation to notification delivery would mean a flaky notification service could block orders. An agent without this context, asked to "improve reliability of the notification flow," might observe that the notification call runs in a daemon thread with no success verification, conclude that this is unreliable, and make the call synchronous so the order response waits for notification confirmation. From the agent's perspective, this is strictly more reliable: the order does not confirm until notification is guaranteed. This satisfies a reasonable definition of "reliable." It also breaks the isolation boundary that was the entire point of the fire-and-forget design. The order service now fails or times out whenever the notification service has a problem. The agent correctly implemented "more reliable notifications" while breaking "reliable order confirmation" — because it had no context about which dependency was supposed to be isolated from which.

**Production-system example:** A payment webhook handler is designed without retry logic. The handler processes payment status updates from a payment provider and updates order records. The design decision — no retries — was deliberate: the payment provider already retries webhook delivery up to 25 times over 72 hours. Adding application-level retries would mean that when the payment provider retries delivery (as it does on any 5xx response), the handler processes the same webhook twice. The order record is updated twice. For status updates that are idempotent, this is harmless. For webhooks that trigger financial operations — refund initiation, commission calculation, fraud flag — duplicate processing means duplicate actions. An agent tasked with "add retry logic to the webhook handler to improve resilience" sees a handler with no retry mechanism and adds one. The payment provider retries. The handler retries. A refund is initiated twice. The agent correctly identified an absence of retry logic. The absence was intentional. Nothing in the handler's code explained why.

**Artifact that prevents it:** Dependency maps and external service contracts in CLAUDE.md or a dedicated architecture document — explicit statements of which external systems this service calls, which external systems call this service, what those callers depend on, and which design decisions were made to manage specific failure modes in those dependencies. An agent cannot discover this from the code; the code shows the calls but not the contracts.

---

### Failure Mode 4: Invariant Blindness

**Definition:** The agent does not know which properties of the system must remain true across all changes — the invariants that were never written down because they seemed obvious to the people who designed the system.

**The mechanism:** Invariants are properties that all implementations of a system must preserve, regardless of how the implementation changes. Some invariants are enforced by tests. Some invariants are enforced by types. The invariants that cause the most damage are the ones that are enforced by convention and institutional memory — the ones that "everyone knows" and nobody documented, because at the time they were established, there was no reason to imagine that anyone would not know them.

**Project example (Issue #2 — inventory before payment):** The order service always checks inventory before calling the payment gateway. This decision was made explicitly in Issue #2 and documented in the Gherkin spec (Scenario 3: payment gateway is never called for out-of-stock items). The ordering is load-bearing: checking inventory first means the payment gateway is never called for orders that cannot be fulfilled. An agent asked to "optimize the order flow" might observe that the inventory check adds latency before the payment call, reason that checking payment first is faster for the common case (in-stock items), and propose reordering the calls. Payment-first, then inventory. Both checks still happen. All five scenarios still pass — Scenario 3 passes because the inventory check still happens, even if it happens after the payment attempt. But the system now charges customers before confirming that their items are available. When inventory is out of stock, the payment has already been processed. The refund path is now required for every out-of-stock order that reaches payment. The spec told the agent what each scenario produces; it did not tell the agent that the ordering of the calls is an invariant, not an implementation detail.

**Production-system example:** A financial transaction flow processes a fraud check and a fund capture in sequence. The fraud check runs first, then the fund capture. This ordering is established practice — fraud detection first is standard in financial systems. Over time, the fraud check becomes a latency bottleneck: it calls a third-party service that has become slow. An agent tasked with "optimize financial transaction latency" identifies the fraud check as the bottleneck and proposes running it in parallel with the fund capture, or running it after the capture completes. The agent is not removing the fraud check — it still runs. The tests still pass — both steps complete. But funds are now captured before fraud is detected. When the fraud check returns a positive result after capture, the transaction must be reversed. Chargebacks increase. The reversal rate creates liability. The test suite does not encode "fraud check must complete before capture" as an assertion — it encodes "fraud check runs" and "capture runs" as separate assertions. The invariant was in the ordering. The ordering was not tested. The agent had no way to know the ordering was non-negotiable.

**Artifact that prevents it:** Invariant documentation — explicit statements of properties that must remain true across all changes to the system, separate from the behavioral specs that describe what the system does. Invariant documentation states constraints on the *implementation*, not just constraints on the *output*. "Inventory must be checked before payment is attempted" is an invariant; "out-of-stock items return 409" is a behavioral spec. Both are necessary. Only the spec is currently encoded in the tests.

---

## Phase 3 — This project's Layer 3 exposure

**Date:** 2026-07-05
**Status:** ✅ Worked

### Production blindness exposure

**Currently exposed:** Yes.

**Specific gap:** `CLAUDE.md` names three ports (8091, 8092, 8093) and their purposes. It does not distinguish between production environments, staging environments, and test environments — because this project does not have a production deployment. But it has a CI/CD pipeline (`ci.yml`) that runs on every push to `main`, and that pipeline uses the same ports and the same service identifiers as local development. There is no document that states which resources an agent may modify, which it may only read, and which it must never touch regardless of context.

**What a Layer 3 artifact would look like:** A new section in `CLAUDE.md` titled "Environments and resource ownership" that lists: the CI/CD pipeline as a shared resource (any change to `ci.yml` affects every contributor's gate, not just the current session), the `pacts/` directory as a derived artifact that must not be manually edited, and the `main` branch as the production equivalent for this project (changes to main that break CI are analogous to production outages in a live system). This section needs to be explicit about what "touching" each resource means — reading it, modifying it, deleting it — and what the protocol is for each action.

---

### Historical amnesia exposure

**Currently exposed:** Yes.

**Specific gap:** Twelve sessions of decisions are documented in `findings/issue-02-*.md` through `findings/issue-13-*.md` as narrative prose. The decisions are accessible — any agent that reads the findings files can recover the reasoning. But findings files are not ADRs. They document what happened; they do not state invariants in a machine-readable format that can be queried by an agent before acting. An agent asked to "improve the timeout behavior" would not automatically read twelve findings files to check whether the 12-second timeout had a documented history. It would read the current step definition, infer the intent, and act.

More specifically: the fire-and-forget decision for the notification service (`issue-07-scope-problem.md`) is documented in prose. The decision to order inventory before payment (Issue #2) is implicit in the Gherkin spec. The decision to not retry the payment gateway more than twice (Issue #2/3) is in a step definition. None of these decisions are in a format that states "this is a decision that must not be reversed without reviewing the documented reasoning."

**What a Layer 3 artifact would look like:** An `ADR/` directory containing decision records for the four or five most load-bearing architectural choices: the fire-and-forget notification design, the inventory-before-payment ordering, the mock server lifecycle ownership (fixtures, not CI YAML), the two-attempt payment retry cap, and the Pact contract as the enforcement mechanism for API shape. Each ADR needs an agent-readable "Do not change without reading this" header that names the downstream consequences of reversal.

---

### Dependency ignorance exposure

**Currently exposed:** Yes.

**Specific gap:** `CLAUDE.md` documents the three services and their ports in a table. It does not document the contracts between them — what fields each service depends on from the others, which failure modes are handled, and which design decisions exist specifically because of a dependency's behavior. For example: the Pact consumer tests encode the fields the order service depends on from the payment gateway (`status`, `transaction_id`, `amount`) — but the reason those specific fields were chosen is not documented. An agent asked to "simplify the payment gateway integration" might remove `transaction_id` from the response contract because it is not used in any business logic visible in `app/main.py`. The Pact tests would catch this — but only if the agent runs them, and only if the agent does not also modify the Pact tests.

**What a Layer 3 artifact would look like:** A dependency map section in `CLAUDE.md` or a dedicated `docs/dependencies.md` that states for each external service: what the order service sends to it, what it must receive back (and which fields are load-bearing vs. informational), which failure modes the order service handles (and which it intentionally does not), and which design decisions were made specifically because of that dependency's behavior. The payment retry cap being 2 because it is 2 total attempts (not 2 retries + 1 original) needs to be in this document, not inferred from a step definition.

---

### Invariant blindness exposure

**Currently exposed:** Yes, and this is the highest-risk gap.

**Specific gap:** The behavioral invariants of the order service are encoded in the Gherkin spec (`tests/features/order_creation.feature`). The implementation invariants — properties of the implementation that must remain true regardless of how the behavioral spec is satisfied — are not encoded anywhere. Specifically:

- The ordering of operations (inventory → payment) is an invariant, not a behavioral preference. It is visible in `app/main.py:create_order()` but not stated as "this ordering must not change."
- The fire-and-forget notification (daemon thread, exception caught silently) is an invariant about isolation. The code makes it fire-and-forget, but nothing states that making it synchronous would violate a design constraint.
- The Pact contract being the authoritative source for API shape is an invariant about governance — the stub can change but the Pact contract must not change without consumer consent. This is documented in the findings but not stated as a system invariant.

**What a Layer 3 artifact would look like:** A short `docs/invariants.md` document with a numbered list of implementation constraints that must survive all future changes. Format: "Invariant N: [property]. [Consequence of violating it]. [How it is currently enforced]." Five to ten invariants is the right scope — if it is longer than that, it is probably documenting behavioral specs rather than invariants.

---

### Why this matters (Layer 3 exposure synthesis)

This project has twelve sessions of documented history and six active skills. Both are significant achievements relative to the state of most AI-assisted projects. Neither addresses the class of failures described in Phase 2. The findings files are too narrative to be queryable. The skills govern how agents produce output; they do not govern what agents must not change. The Gherkin spec constrains behavior; it does not constrain implementation structure. An agent starting Issue #15 with access to all of this infrastructure could still reorder the inventory and payment calls, make the notification call synchronous, remove a Pact field that looks unused, or push to a branch that triggers the CI gate — not because the infrastructure is inadequate for what it was designed to do, but because none of it was designed to answer the question "what must not change?"

---

## Phase 4 — The artifact map

**Date:** 2026-07-05
**Status:** ✅ Worked

See `docs/layer3-artifact-map.md` (created this session).

---

## Phase 5 — The argument for Layer 3

**Date:** 2026-07-05
**Status:** ✅ Worked

### The argument for Layer 3

Twelve issues in, this project has a working API, a full Gherkin test suite, Pact contracts for both downstream dependencies, a CI/CD pipeline with four blocking jobs, and a skill layer with six active skills across three tiers. That is more infrastructure than most projects of this scope ever build. It is not enough.

Here is the specific moment that makes this clear. In Issue #3, the agent was given only the Gherkin feature file and asked to build the order service from scratch. It derived the complete API contract — all five response shapes, all status codes, the correct timeout/retry logic — from plain-language scenario descriptions alone. It also found a portability bug in the original test harness that the human author had missed. These are genuinely impressive capabilities. The spec did its job; the agent did its job; the output was correct.

Now consider what would have happened if the task in Issue #3 had been slightly different. Not "build the order service from this spec" but "optimize the order service." Same agent. Same codebase. But the framing shifts from implementation to modification. The agent reads `app/main.py`. It sees the inventory check before the payment call. It reasons: for the common case (items in stock), this means the payment gateway is called on every order anyway — you could check payment first and skip inventory for the 95% of orders that succeed. That is a reasonable inference. It is also wrong, because the spec has an explicit invariant: the payment gateway must never be called for out-of-stock items. The agent knows this from Scenario 3. But "never called for out-of-stock items" does not imply "inventory must be checked first" — it only implies that if inventory is checked and fails, payment must not be called. An agent that checks payment first and then inventory, cancelling the payment if inventory fails, satisfies Scenario 3 while violating the design intent. And it would not know it violated the design intent, because the design intent was never written as a constraint on implementation structure.

Or consider Issue #7. The notification service is fire-and-forget because coupling order confirmation to notification delivery is a failure mode, not a feature. An agent asked to "add observability to the notification flow" would add it. An agent asked to "ensure notifications are delivered reliably" might make the call synchronous — because synchronous delivery is strictly more reliable than fire-and-forget. The spec does not forbid this. The tests do not catch it. The skills say nothing about it. The only thing that would prevent it is a document that states, explicitly: the notification call must remain asynchronous; synchronous notification delivery is a failure mode, not an improvement; here is why.

The spec tells the agent what to build. The skill tells the agent how to reason about the build. Neither tells the agent what must never change, what happened before the agent arrived, or which external systems it is silently affecting by changing something that looks local. The spec is a contract for output. The skill is a contract for process. Layer 3 is the contract for the past — the accumulated weight of decisions that were made by people who are no longer in the session, for reasons that seemed obvious at the time, and that the system now depends on in ways that nobody wrote down.

Twelve issues in, this project is ready to confront what it cannot prevent. That is what Layer 3 is for.

---

## Phase 6 — Test suite verification

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Ran the full test suite — Gherkin, Pact consumer, Pact provider, and can-i-deploy — to confirm that a documentation-only session leaves all 15 tests passing.

### What happened

```text
pytest tests/steps/ -v
→ 11 passed

pytest tests/pact/ -v
→ 4 passed (inventory consumer, payment consumer, payment provider, inventory provider)

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

All 15 tests pass. No implementation files were modified.

### Why this matters

A documentation session that breaks a test is a documentation session that made a claim and then proved it wrong. Running the full suite after a research-and-documentation session is the equivalent of running `cargo check` after a comment-only edit — probably fine, but the cost of checking is lower than the cost of being wrong.
