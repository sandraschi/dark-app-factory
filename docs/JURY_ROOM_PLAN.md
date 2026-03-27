# Jury Room Plan — Expert Panel Meta-Judge

**Status**: Planned for March implementation  
**Inspiration**: *12 Angry Men* (1957) — deliberation, persuasion, bias, diverse perspectives  
**Current State**: Single "Judge Dee" superjudge (LLM verdict on audit evidence)

---

## Concept

Replace or augment the single LLM verdict with a **panel of 12 expert personas** that deliberate over the same evidence (audit report, scenario results, satisfaction score, lint report, DTU logs). Each expert has distinct domain focus, temperament, and preconceptions. They argue, challenge, and surface different concerns. Instead of a binary GUILTY/NOT GUILTY vote, they produce **elaborated analysis** across dimensions (usability, aesthetics, correctness, security, performance, maintainability). The Judge (meta-layer) synthesizes the analysis into a final go/no-go and critique.

---

## Architecture

```
Evidence Docket (input)
  ├── Auditor report
  ├── Satisfaction report (scenario execution)
  ├── Ruffy lint report
  ├── UI/Execution report (Rodney/Playwright)
  ├── DTU logs
  └── Files generated (summary)

        │
        ▼
┌─────────────────────────────────────┐
│    EXPERT PANEL (12 Personas)       │
│  Simulated deliberation via LLM     │
│  Each produces domain-specific      │
│  analysis (UX, security, perf, etc) │
└─────────────────────────────────────┘
        │
        ▼
  Elaborated Analysis (structured report)
  - What works / what's weak / what to fix
  - Per-dimension assessments
  - Final recommendation (go / no-go / conditional)
        │
        ▼
┌─────────────────────────────────────┐
│   JUDGE (synthesis + critique)      │
│   Converts analysis -> critique.md  │
│   Passes gate (PASS/FAIL)           │
└─────────────────────────────────────┘
```

---

## The 12 Expert Personas — Spec

| # | Name / Archetype | Domain Focus | Temperament | Output |
|---|------------------|--------------|-------------|--------|
| 1 | **Foreman** | Orchestration | Procedural, seeks consensus | Summarizes panel findings, synthesizes |
| 2 | **Reasonable Doubt** (Fonda) | Cross-cutting | "What if we're wrong?" | Surfaces risks, questions assumptions |
| 3 | **UX Advocate** | Usability, flows | User-first, empathetic | Usability analysis, user-journey gaps |
| 4 | **Analyst** | Correctness, data | Logic, evidence-only | Scenario pass rates, data consistency |
| 5 | **Designer** | Aesthetics, layout | Opinionated, visual | UI/UX assessment, accessibility notes |
| 6 | **Skeptic** | Quality bar | "Prove it works" | Scenario evidence, edge cases |
| 7 | **Security** | Auth, data handling | Paranoid | Security concerns, validation gaps |
| 8 | **Pedant** | Standards, lint | Detail-oriented | Ruff/mypy, formatting, conventions |
| 9 | **Performance** | Speed, scalability | Engineering-minded | Bottlenecks, lazy-loading, caching |
| 10 | **Cynic** | Reality check | "Apps always fail" | Worst-case, failure modes |
| 11 | **Architect** | Structure, maintainability | Holistic | Code organization, coupling, future-proofing |
| 12 | **Pragmatist** | Ship decision | Cost/benefit | Go / no-go recommendation, priorities |

---

## Deliberation Protocol

1. **Evidence distribution**  
   Each expert receives the full evidence docket (truncated/summarized for token budget).

2. **Initial assessments**  
   Each expert writes a short domain-specific analysis: strengths, weaknesses, concerns. Structured fields (e.g. UX score 1–5, issues list, recommendation).

3. **Rounds of debate**  
   - Rounds 1–2: Experts challenge, rebut, cite evidence. Persona 2 (Reasonable Doubt) must surface at least one "what if we're wrong?" angle.  
   - Constraint: Max N tokens per expert per round; max K rounds.

4. **Elaborated analysis (output)**  
   Each expert finalizes:
   - **Domain assessment** (e.g. Usability: 4/5, "Good flows but login unclear")
   - **Top issues** (ranked, actionable)
   - **Recommendation** (approve / conditional / reject)

5. **Foreman synthesis**  
   Aggregates into structured report: per-dimension scores, consolidated issues, final go/no-go with rationale.

6. **Judge critique**  
   Single LLM call: Given the panel report, Judge writes critique.md and gate decision (PASS/FAIL).

---

## Implementation Sketch (March)

- **Mode**: Optional. `judge.py --mode panel` vs `--mode single` (current).
- **LLM usage**: 12 personas = 12 system prompts. Debate:
  - **Parallel**: Each expert responds to same evidence in one batch; aggregate; next round. (Faster.)
  - **Sequential**: Expert 1 → 2 → … → 12, each sees prior analyses. (Slower, more realistic.)
- **Persona prompts**: Structured: "You are Expert N (UX Advocate). Domain: usability. Evidence: … Output: domain_assessment, top_issues, recommendation."
- **Output format**: JSON or markdown sections per expert; Foreman aggregates into final report.
- **Token budget**: ~50k for evidence; ~2k per expert per round × 12 × 2 rounds = ~48k. Summarization if needed.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Token cost 12× | Use cheap/small model for experts; Judge only for final synthesis |
| Degenerate debate (all agree immediately) | Inject contrarian prompts; require minimum rounds; diverse persona instructions |
| Unpredictable output format | Structured JSON/markdown schema; validation before Judge step |
| Slow (minutes) | Parallel expert calls; cap rounds; optional mode |

---

## Relation to Current Judge Dee

- **Judge Dee** = single strict QA Lead LLM. Fast, deterministic given model.
- **Expert Panel** = meta-layer: 12 domain experts produce elaborated analysis, then Judge synthesizes into critique and gate.
- **Hybrid**: Run both; panel report informs Judge's tone and priorities (e.g. "Panel flagged UX and security; focus critique there").

---

## References

- *12 Angry Men* (1957), dir. Sidney Lumet — deliberation, persuasion, diverse temperaments
- Henry Fonda as Juror 8 — reasonable doubt, persistent questioning (adapted as "Reasonable Doubt" persona)
