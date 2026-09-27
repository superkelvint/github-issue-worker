# CTO Reflection — <date/window>

## Executive summary

Give 2–4 sentences naming the biggest process lesson and the most useful change to make now.

## Highest-leverage findings

Use a compact table when there are several findings:

| Pattern | Evidence | Root cause | Durable fix | Action |
|---|---|---|---|---|
| ... | recurring / one-off + thread examples | skill/tooling/workflow/habit | concrete change | do now / recommend / observe |

Keep this section ordered by leverage, not chronology.

## Skill changes

For each relevant skill:

- **Skill:** name
- **Observed failure:** what conversations showed
- **Change:** exact behavioral instruction/trigger/workflow improvement
- **Status:** implemented and packaged / recommended only

If no skill should change, say so. Do not invent a skill change to fill the section.

## CTO/user feedback

Give only evidence-backed behavioral feedback. Split naturally into what to keep and what to change if both matter. Avoid generic productivity advice.

## Process/tooling actions

List concrete repository/workflow/automation changes that are outside skill scope. Include the likely owner/location when known.

## False-green check

Name any proposed optimization that could weaken verification and the guardrail required to make it safe. Omit this section only when no such risk is material.

## Next reflection

State 1–3 observable signals to check in the next reflection, such as:

- number of threads requiring a second "continue/check again" prompt;
- whether affected PRs were automatically/reliably caught up after a main fix;
- whether unrelated CI fanout recurred;
- whether a changed skill triggered and reached closure without human nudging.
