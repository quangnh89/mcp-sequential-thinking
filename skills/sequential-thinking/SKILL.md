---
name: sequential-thinking
description: "A notebook for structured step-by-step reasoning: it records and stages the reasoning you write, it does not think for you. Use it selectively, on hard decisions - never as a gate or a deliverable. Triggers: think through, step by step, break this down, sequential thinking, reason through, analyze step by step, think carefully."
license: MIT
---

`sequential-thinking` is a **notebook, not a brain**. There is no model inside it: it records the
reasoning *you* write, stages it (Problem Definition → Research → Analysis → Synthesis →
Conclusion), tracks revisions and branches, and can summarize the result. Its value is that a hard
decision becomes inspectable — what you assumed, what you challenged, where you changed your mind —
not that it produces an answer.

Two consequences that decide how to use it:

- **The durable record is elsewhere.** The deliverable is the real artifact of the work — the
  manuscript, the thesis chapter, the pull request, the analysis memo, the journal entry, the
  ticket. Copy the Conclusion into it. A thought chain is a transient scratchpad and is never the
  deliverable.
- **It is never a gate.** A `Conclusion` thought authorizes nothing. The real gates are the tests,
  the CI run, the code review, the reconciliation against the source figures, the editor. "I
  concluded it's done" is not evidence.

## When to open a chain — and when not to

| Open a chain | Skip it |
|---|---|
| A decision that is **costly to reverse** — the shape of a schema migration, committing to a library, the ending a plot has to earn | A choice with an obvious default, or one you can cheaply undo |
| **Sources that disagree** — two reports that will not reconcile, logs that contradict the code, two references citing different figures | A fact you can look up once (that is a docs or search tool) |
| A **multi-step argument someone must be able to audit later** — a valuation, a thesis claim built from data, a data-flow path | A step you can state in one sentence |
| **Ranking candidates or synthesizing across areas** — which lead, which vendor, which chapter order | Mechanical, repetitive edits |
| **Inferring a rule from indirect evidence** — an undocumented API, the right treatment for an unusual transaction, a character's established motives | Anything where you would write the same five words five times |
| A judgement you expect to **defend or revisit** — a close call between two readings | Work whose result is self-evident once produced |

Recording "the total is the sum of the lines" as five staged thoughts is pure overhead — and it
costs context the actual work needs. A workflow layered on top of this skill may make the notebook
mandatory for its whole protocol; when it does, it is no longer selective. This skill imposes no
such requirement on its own.

## Tools

| Need | Tool |
|---|---|
| Record one reasoning step | `process_thought` |
| Overview of the chain so far (stages, timeline, branches, top tags) | `generate_summary` |
| Wipe the history | `clear_history` — see the warning below |
| Persist / restore a chain across a session boundary | `export_session`, `import_session` |
| See which stores exist on the server, and how big | `list_sessions` |

Every one of them except `list_sessions` takes a `session` — the store it operates on. See "One
store per unit of work" below; **pass it on every call.**

The names above are the ones the server registers. Whether your host exposes them bare or behind a
prefix is a property of the installation, not something to decide while reasoning: this copy was
normalized for its host at install time.

## `process_thought` parameters

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `thought` | string | yes | The substantive reasoning. Analytical and explicit — a reader must follow it without your context. |
| `thought_number` | int | yes | Position in the sequence, starting at `1`. |
| `total_thoughts` | int | yes | Current estimate of the total. Must be `>= thought_number`. Adjust it as understanding changes. |
| `next_thought_needed` | bool | yes | `false` only on the final thought of a finished chain. |
| `stage` | string | yes | Exactly one of `Problem Definition`, `Research`, `Analysis`, `Synthesis`, `Conclusion`. |
| `session` | string | in practice yes | The store this chain belongs to — **one stable id per unit of work**: a repository or service, a manuscript, a ticker plus period, an audit file, a ticket. See "One store per unit of work" below. |
| `tags` | string[] | no | **Always pass a stable key for the thing under analysis** plus a topic — e.g. `["orders.checkout", "latency-regression"]`, `["ch12", "continuity"]`. Tags slice one subject out of a unit of work's chain; `session` is what separates the units of work. |
| `axioms_used` | string[] | no | Invariants you applied (e.g. `"evidence before conclusion"`, `"revenue is recognized on delivery"`). |
| `assumptions_challenged` | string[] | no | Beliefs you are questioning or dropping. Fill this at every course change. |
| `is_revision` | bool | no | This thought corrects an earlier one. |
| `revises_thought_number` | int | no | Which thought it corrects. |
| `branch_from_thought` | int | no | Fork point for an alternative line of reasoning. |
| `branch_id` | string | no | Name of that branch, e.g. `demand-shift`. |

**Cross-field rules the server enforces** — violate one and the call is rejected, not corrected:

- `is_revision: true` requires `revises_thought_number`, and `revises_thought_number` requires
  `is_revision: true`.
- A thought cannot be a revision *and* a branch start.
- `branch_id` requires `branch_from_thought`.
- `revises_thought_number` / `branch_from_thought` must satisfy `1 <= n < thought_number`.
- `branch_id`: 1–64 characters from `[A-Za-z0-9_-]` only.

Revisions and branch thoughts do **not** advance progress — only mainline thoughts count towards
`total_thoughts` — so correcting yourself never inflates completion past 100%.

## The stages

| Stage | Goal |
|---|---|
| `Problem Definition` | The exact question and its hard constraints. What would count as an answer? |
| `Research` | Evidence gathered — code read, source documents, measurements, statements, doc lookups. Facts, with citations (`file:line`, a URL, a document id, a chapter and paragraph). |
| `Analysis` | Correlate the evidence, build competing hypotheses, find the root cause or the trade-off. |
| `Synthesis` | Combine into one coherent reading and test it against the evidence that must also hold. |
| `Conclusion` | State the outcome and what it licenses — then execute it, and let the real gate decide. |

Never move past `Research` on a guess. If the evidence is missing, go and get it rather than
reasoning around the hole.

## One store per unit of work — the `session` parameter

The server keeps a **separate history per session namespace**, and every call decides which one it
lands in. Name it the same way each time and one unit of work's reasoning stays one chain, no matter
how many agents, machines or runs contribute to it.

**What to pass:** one stable id for the unit of work — the repository or service name, the
manuscript, the ticker plus period, the audit file, the ticket number. Pick the naming rule once and
apply it mechanically; an orchestrator hands the string to its subagents rather than letting each
one invent it.

A call that names no session is **refused**, not quietly merged — the server answers
`No thinking session resolved` and stores nothing. Three ways it can be named, first one wins:
the `session` argument (what you should do), the `X-Thinking-Session` header or `?session=` on the
server URL (a per-deployment default someone set in the MCP client config), or the server's
`MCP_DEFAULT_SESSION`. The response echoes the store it used at
`thoughtAnalysis.context.session` — read it once at the start of a chain to confirm you are writing
where you think you are.

A misspelled name is not an error: it silently opens a **new, empty** store. `list_sessions` is how
you notice (it lists every store with its thought count).

Inside one session, several agents still share the history — an orchestrator with 3–4 subagents on
the same unit of work is the normal case — so these still hold:

1. **Tag every thought with a stable key.** `session` separates units of work; tags are what slice
   one subject's reasoning back out of a unit's stream. An untagged thought is effectively lost.
2. **Do not call `clear_history` while other agents may be running.** It does not touch other
   sessions, but it wipes everyone working on *this* one. Under an orchestrator the answer is
   never. It is defensible only when you are provably alone in that session.
3. **`import_session` replaces a session's history**, it does not merge. Within a session it is as
   destructive as `clear_history`; treat it with the same rule.
4. **`generate_summary` covers the whole session, not your chain.** With other agents alive its
   `stages`, `timeline`, `branches`, `revisionCount` and `percentComplete` mix in their thoughts.
   Read it as a rough indicator; never paste it into a deliverable as if it described your chain
   alone. `percentComplete` is `mainline count / largest total_thoughts` **across every chain in
   that session**, so it can still read over 100%.
5. **Back-references resolve by number, within the session.** `revises_thought_number` and
   `branch_from_thought` are matched against every mainline thought in that session's history — not
   against your chain — so the `revisionOf` snippet the server echoes back (and the
   `relatedThoughtSummaries` beside it) can belong to a co-worker's thought that happens to carry
   the same number. What you *stored* is still correct; it is the echo that is unreliable, so read
   the response's snippets as a hint and never as confirmation that you revised the thought you
   meant to.

## Export / import are confined to the server's storage

`export_session` and `import_session` resolve a relative `file_path` inside that session's own
`exports/` subdirectory (`<storage>/spaces/<session>/exports/`), and reject any path that escapes it
(a deliberate path-traversal guard). That storage lives on the **MCP server host**, not on the
machine running the agent — an exported file is not one you can then open with a file read. Use them
to carry a chain across a session boundary; the durable artifact remains the real deliverable.

## References

- [examples.md](references/examples.md) — three full chains, one per pattern: a web/database
  regression that corrects itself, a price-and-volume analysis explored as branches, and a
  manuscript continuity chain carried across a session boundary.
- [patterns.md](references/patterns.md) — revision vs. writing on, branch-and-converge, scope
  adjustment, concurrency, export/import.
