---
name: cto-reflection
description: Review the user's recent SearchKernel/CTO conversations, normally the last 24 hours, and turn observed friction into concrete process improvements. Use for requests such as "CTO reflection", "reflect on yesterday", "what slowed us down", "how can we streamline the CTO process", or "improve our skills/workflow based on the last day". Inspect actual recent conversations, current SearchKernel CTO workflow/repository rules, and relevant installed skills; identify repeated waste, false-green risks, missing automation, weak skill behavior, and user/CTO habits; then recommend or, when safely justified, draft improved/new skills.
---

# CTO Reflection

Run an evidence-driven retrospective on how the SearchKernel CTO process actually behaved, not on how it was intended to behave.

Default to the previous 24 hours unless the user gives another window. Optimize for fewer unnecessary turns, less repeated investigation/build work, faster issue/PR flow, and stronger closure without weakening verification.

## Workflow

1. **Collect the evidence window.**
   - Retrieve the user's relevant conversations from the requested period. Prefer actual conversation retrieval/history over remembered summaries when available.
   - Include the current conversation when it falls in scope.
   - Focus on SearchKernel development, review, issue/PR management, CI/tooling, skills, and CTO workflow unless the user asks for a broader reflection.
   - If conversation retrieval is incomplete, state the gap and do not pretend the sample is exhaustive.
   - If a previous CTO reflection exists, retrieve the most recent one and check whether its proposed changes were attempted and whether the same friction recurred.

2. **Refresh authoritative project rules before judging the process.**
   - For substantive SearchKernel conclusions, fetch the current `WORKFLOW.md` from `main` in `superkelvint/searchkernel-cto-state`.
   - Fetch the current `AGENTS.md` from `main` in `superkelvint/searchkernel`.
   - Read `STATUS.md`, `ISSUE_LABELS.md`, `docs/roadmap.md`, or other current control-plane files only when the observed friction depends on them.
   - Do not rely on a remembered workflow when current repository state is available.

3. **Inspect relevant skills when skill behavior may be causal.**
   - List/read the currently installed skill whose trigger or workflow should have handled the repeated task.
   - Check whether the problem is missing instructions, poor trigger wording, duplicated responsibilities, excessive clarification, lack of closure behavior, or a missing skill entirely.
   - Do not recommend a new skill when a small improvement to an existing skill would solve the recurring problem.

4. **Reconstruct the day's work as process events.**
   For each meaningful thread, identify internally:
   - intended goal;
   - number/type of user nudges needed to reach it;
   - avoidable stalls or repeated checks;
   - tool/build/CI work repeated unnecessarily;
   - where the assistant stopped before natural closure;
   - where the user had to restate an already-known requirement;
   - any false-green or verification gap;
   - what finally resolved the friction.

5. **Cluster root causes, not symptoms.**
   Use the rubric in `references/reflection-rubric.md`.
   Prefer repeated patterns across multiple threads. A single incident can still matter when severity or blast radius is high.

6. **Choose the narrowest durable fix.**
   Classify each recommendation as one of:
   - **skill change** — reusable agent behavior is missing or wrong;
   - **new skill** — a distinct repeatable workflow is genuinely absent;
   - **repository tooling** — a command, CI selector, cache, runner, script, or environment contract is the cause;
   - **CTO workflow/control plane** — issue/PR lifecycle, labels, verification, or reconciliation rules are the cause;
   - **automation** — repeated polling/checking has a clear future trigger or cadence;
   - **user/CTO habit** — prompt/scoping/decision behavior is the main leverage point;
   - **no change** — isolated annoyance or a fix would add more machinery than it removes.

7. **Challenge every proposed improvement for false-green behavior.**
   Before recommending a shortcut or automation, ask how it could make the process look faster while silently weakening correctness. Examples:
   - narrower CI that misses semantic dependencies;
   - a convenience command that silently skips required tests;
   - a skill that auto-merges before exact-head verification;
   - caching that reuses stale generated/native artifacts;
   - queue filters that strand valid work;
   - automation that repeats stale or duplicate actions.
   Reject or qualify improvements that trade visible friction for hidden risk.

8. **Apply a skill change only when the evidence is strong and the intent is unambiguous.**
   - Prefer making a concrete change when the same reusable failure recurred, the desired behavior is clear from authoritative rules and user intent, and the change is local to a skill.
   - Use the `skill-creator` skill for any creation or update. Package the complete resulting skill, not a patch fragment.
   - Do not silently redesign architecture, project contracts, CI policy, or the CTO workflow merely because a conversation was frustrating. Recommend those changes unless the user explicitly authorized implementation.
   - If two skills overlap, prefer clarifying ownership/triggers over adding a third overlapping skill.

9. **Close with prioritized actions.**
   Produce a concise reflection using `references/report-template.md`. Lead with the highest-leverage findings, not a chronology of conversations.

## Evidence standards

- Tie every material finding to one or more observed threads from the requested window.
- Distinguish **recurring pattern**, **high-severity one-off**, and **hypothesis**.
- Do not infer that user frustration alone proves the proposed root cause; trace the actual process failure.
- Do not call a process successful merely because the final PR merged. Include excess turns, repeated builds, stale state, wrong CI fanout, follow-up repair, or reconciliation work when relevant.
- Treat assistant/agent claims and green CI as evidence to inspect, not truth.
- Prefer changes that remove an entire class of repeated prompts over wording tweaks that only make one prompt nicer.

## Skill-change decision rule

A skill change is usually warranted when at least one is true:

- the user had to give the same operational instruction more than once in the window;
- multiple threads exposed the same missing proactive step;
- a skill repeatedly stopped at "ready" when the intended workflow required closure/reconciliation;
- the same task required rediscovering a known command, label, path, or invariant;
- the skill's trigger failed to route a clearly matching request;
- the skill caused redundant permission/clarification/tool-discovery steps that can be eliminated safely.

Do not modify a skill merely because one execution was slow or a repository/environment defect happened underneath it.

## Operating tone

Be concise, specific, and willing to say that a process or user habit is causing waste. Avoid generic retrospective advice. Prefer concrete statements such as "three PR threads required a second prompt to re-check CI after a main fix; make re-check-after-rebase part of PR closure" over "be more proactive."

## Deterministic policy helper

Use `scripts/reflection_policy.py` as the deterministic reference for recurring-vs-one-off evidence strength, narrowest durable-fix classification, preferring an existing skill over a new overlapping one, automation eligibility, and false-green shortcut rejection. The actual retrospective still requires qualitative analysis of the retrieved conversations.

After changing reflection policy, run:

```bash
python3 -m unittest discover -s cto-reflection/scripts -p "test_*.py" -v
```
