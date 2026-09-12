# Patterns

How to use the notebook's mechanics well, once you have decided a chain is worth opening at all
(SKILL.md, "When to open a chain").

Each pattern below is illustrated by exactly one running scenario, and each of those scenarios is a
complete chain in [examples.md](examples.md) — same story, same `session`, same tags.

| Scenario | `session` | Pattern it carries | Chain |
|---|---|---|---|
| A checkout endpoint's latency regressed after a release | `checkout-service` | Revision; Scope | Example A |
| A quarter's price rise came with a volume spike | `ACME-2025Q3` | Branch and converge | Example B |
| A novel's chapter 12 has to keep its continuity straight | `thornfield-manuscript` | Export / import | Example C |

## Revision: correcting, not continuing

Set `is_revision` + `revises_thought_number` when new evidence makes an earlier thought **wrong**.
Just writing the next thought is right when the earlier one was merely incomplete.

Scenario: the `checkout-service` latency regression.

| Situation | What to do |
|---|---|
| A measurement with the cache warmed refutes the "the regression is cache-miss cost" claim you made in thought 3 | Revision of 3 |
| You find a second endpoint with the same query-count symptom, which adds detail to thought 3 | Plain next thought |
| The `order_total` column you called the source of truth in thought 2 turns out to be a denormalized copy | Revision of 2 |
| You switch from reading the schema to reading the query plan | Plain next thought (usually a stage change) |

Two things follow from the server's model:

- The response echoes a `revisionOf` block with the revised thought's stage and a snippet. Treat it
  as a hint only: the lookup is by thought NUMBER across the whole session, so with co-workers in
  the same session it can echo their thought back at you (SKILL.md, rule 5).
- Revisions do not advance progress. Only mainline thoughts count against `total_thoughts`, so a
  chain that corrects itself three times still reports a sane percentage.

Put the belief you are abandoning in `assumptions_challenged`. That field is what makes a chain
worth re-reading months later — a list of the things that looked true and were not. Example A walks
this through end to end.

## Branch and converge

A branch is a hypothesis you intend to kill or keep, not a place to park a thought.

Scenario: `ACME-2025Q3`, where price and volume both rose and two readings fit the same signature.

1. Fork from the thought that poses the alternatives: `branch_from_thought: <n>` +
   `branch_id: "<name>"` (`[A-Za-z0-9_-]`, ≤64 chars) — here `demand-shift` and `supply-shock`.
2. Give each branch its own `branch_id` and develop them one at a time — a half-explored branch is
   worse than none, because it reads as an open question that was actually never asked.
3. **Close it on the mainline.** A later mainline thought states which branch survived and on what
   evidence — a figure you can cite to its source, never an impression. `generate_summary` reports a
   `branches` object with each branch's fork point and thought count; use it to catch a branch you
   opened and abandoned.

Name branches after the thing in dispute (`demand-shift` / `supply-shock`), not after their outcome.
Example B is this chain in full, including the thought that kills one of the two.

## Scope: `total_thoughts` is a progress indicator

Start at 4–6. Raise it when a layer of complexity appears — in Example A, at thought 4, once the
cause turns out to sit in the ORM's lazy loading rather than in the SQL being read, because that
layer has to be read before the chain can end. Lower it when the answer arrives early. It must
always be `>= thought_number`, and it is not a plan you owe anyone — an estimate that never moved
usually means the chain stopped being written honestly.

## Concurrency: one store per unit of work, many agents inside it

`session` separates the units of work; inside one the store is still shared (SKILL.md, "One store
per unit of work"). The three sessions above are three stores: `checkout-service`, `ACME-2025Q3` and
`thornfield-manuscript` never share a string, however many agents work in each. In practice:

- **Pass the same `session` on every call of a run.** Two units of work analyzed side by side must
  never share one string, and an orchestrator hands its subagents the string rather than letting
  each invent one.
- **Tag with a stable key, every time.** `["orders.checkout", "latency-regression"]`,
  `["ch12", "continuity"]`. With several agents alive in one session, the tag is the only thing
  separating your reasoning from theirs.
- **Treat `generate_summary` as a shared, noisy view.** Its counts include the other agents working
  that session. It is useful for "did I leave a branch open?", not for "how far along am I?".
- **`clear_history` is a shared-state mutation.** Never under an orchestrator. Acceptable only when
  you are provably alone in that session and the accumulated history is actively misleading you.
- **Check the store you landed in when a chain starts.** The response carries
  `thoughtAnalysis.context.session`; `list_sessions` shows every store with its thought count, which
  is how a typo'd session name (a new, empty store — not an error) surfaces.

There is no way to delete one thought or one chain: the tool is all-or-nothing within a session.
Plan on writing carefully rather than tidying up afterwards.

## Export / import across a session boundary

`export_session` writes that session's whole history; `import_session` replaces it with a file's
contents. Both resolve `file_path` **inside the session's own storage** (relative paths land in
`spaces/<session>/exports/`; anything that escapes is rejected), and that storage is on the MCP
server host — not the machine running the agent.

Scenario: `thornfield-manuscript`. The continuity chain — who knows what by which chapter, which
promises to the reader are still unpaid — took a session to build and the work stops mid-chapter.
Export at the pause, import on resume, and chapter 12 starts from the reconstructed context instead
of rebuilding it from the manuscript. The same shape covers a hand-off between two phases of one
piece of work.

Two cautions: `import_session` **replaces** the session's history, so it carries the same
other-agents' warning as `clear_history` — import only into the session you exported from, and only
when you are alone in it; and an export is not a deliverable. What survives the work is the
manuscript, the pull request, the memo. An export at most restores your scratchpad. Example C ends
on exactly this call.
