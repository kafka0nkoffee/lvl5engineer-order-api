# Order API Knowledge Bundle

This is the OKF v0.1 knowledge bundle for the `lvl5engineer-order-api` project — the living codebase behind [The Level 5 Engineer](https://thelevel5engineer.com) newsletter.

The bundle documents 20 sessions of infrastructure-first AI-assisted development: the Gherkin specs, architecture decisions, agent guardrails, incident runbooks, and skill library that make safe agent-driven implementation possible. It is read by Claude Code agents at session start and by human engineers during incident response and skill review.

---

# Subdirectories

* [ADR/](ADR/) — Architecture Decision Records: load-bearing design decisions with agent check questions and dangerous-improvements lists
* [evals/](evals/) — Pre-flight guardrails: three evals that intercept high-risk modifications before any code is written
* [runbooks/](runbooks/) — Incident playbooks: agent-executable and human-executable runbooks for operational failure scenarios
* [skills/](skills/) — Methodology library: three-tier skill architecture for Gherkin, formatting, session management, and writing

---

# Root-level concept documents

* [Layer 3 Artifact Map](layer3-artifact-map.md) — Maps the four agent failure modes from Issue #14 to the five artifact types built in Issues #15–18.
* [Spec Audit Framework](spec-audit-framework.md) — Structured tool for finding spec debt in Gherkin feature files before it causes production incidents.
* [The J-Curve Conditions Framework](jcurve-conditions-framework.md) — Decision framework for predicting whether infrastructure-first AI-assisted development will return its investment cost in a given project.
* [Skill Review Checklist](skill-review-checklist.md) — Five-dimension checklist for reviewing skill artifacts before publishing a new skill version.
* [Skill PR Template](skill-pr-template.md) — Pull request template for publishing new skill versions, linking each section to the five-dimension skill review checklist.
* [Prompt Library Audit Template](skill-audit-template.md) — Reusable template for auditing accumulated prompt material in any AI-assisted project.
* [CLAUDE.md — Naive Version](claude-md-versions/naive.md) — Pedagogical example of the CLAUDE.md most projects start with on day one.
* [CLAUDE.md — Better Version](claude-md-versions/better.md) — Pedagogical example of an improved CLAUDE.md incorporating permissions modeling and architectural decision references.
* [CLAUDE.md — Production-Grade Version](claude-md-versions/production-grade.md) — Pedagogical example of a production-grade CLAUDE.md with environment discrimination, architectural invariants, and a decision index.

---

# Bundle log

See [log.md](log.md) for the full update history.
