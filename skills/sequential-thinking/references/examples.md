# Three worked chains

One chain per pattern in [patterns.md](patterns.md) — same scenario, same `session`, same tags.
Read them for the *rhythm* — one thought per decision, evidence before conclusion, a stable key in
every tag — not as templates to fill in.

| Chain | Scenario | `session` | Pattern it demonstrates |
|---|---|---|---|
| Example A | A checkout endpoint's latency regressed after a release | `checkout-service` | Revision; Scope |
| Example B | A quarter's price rise came with a volume spike | `ACME-2025Q3` | Branch and converge |
| Example C | A novel's chapter 12 has to keep its continuity straight | `thornfield-manuscript` | Export / import |

Each block is the argument object for `process_thought`. `session` is the same string on every
thought of a run, which is what keeps one chain out of another's summaries and back-references.

---

## Example A — a latency regression, corrected mid-chain

`POST /orders/checkout` went from a 180 ms p95 to 1.4 s after the 2026-08-14 release. The chain has
to name a cause, and it gets the cause wrong once before it gets it right.

### 1 — frame it

```json
{
  "thought": "p95 for POST /orders/checkout moved from 180ms to 1.4s between the 08-13 and 08-14 deploys; p50 barely moved (95ms -> 130ms). Two things must come out of this chain: a cause tied to a specific change in that release, and a measurement that moves when the cause is removed. A plausible story with no measurement behind it does not count as an answer. Constraint: no schema migration before the next release train, so a fix that needs one is a different proposal.",
  "thought_number": 1,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Problem Definition",
  "session": "checkout-service",
  "tags": ["orders.checkout", "latency-regression"]
}
```

### 2 — gather evidence before theorising

```json
{
  "thought": "The release diff touches three things on this path: the line-item Redis cache was removed (commit 4c1f9a2), the checkout serializer now includes line items (api/serializers/checkout.py:88), and orders.order_total is now read rather than recomputed. Schema: orders has 4.1M rows, order_line_items 38M, indexed on order_id. order_total is written by the pricing service on order creation and is the value checkout reports.",
  "thought_number": 2,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Research",
  "session": "checkout-service",
  "tags": ["orders.checkout", "latency-regression"],
  "axioms_used": ["evidence before conclusion"]
}
```

### 3 — a hypothesis...

```json
{
  "thought": "Commit 4c1f9a2 removed the cache that served line items, so every checkout now recomputes them from order_line_items. That is the regression: the cost is cache-miss cost, and restoring the cache restores the p95.",
  "thought_number": 3,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "checkout-service",
  "tags": ["orders.checkout", "latency-regression"]
}
```

### 4 — ...that the measurement kills

This is what `is_revision` is for: not "I want to add more", but "thought 3 is wrong". It also
raises `total_thoughts`, because a layer that has to be read appeared.

```json
{
  "thought": "Wrong. I warmed the cache in staging and replayed the same traffic: p95 stayed at 1.3s. APM says 47 database round-trips per checkout against 3 before the release, all of them the same single-row select on order_line_items. That is an N+1 introduced by the serializer change -- the ORM lazy-loads the association per line -- not cache-miss cost. Raising the scope because the ORM mapping layer now has to be read, not just the SQL. Also correcting thought 2's reading of order_total: it is a denormalized copy written by the pricing service, not the source of truth, so it is not safe to reconcile against here.",
  "thought_number": 4,
  "total_thoughts": 6,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "checkout-service",
  "tags": ["orders.checkout", "latency-regression"],
  "is_revision": true,
  "revises_thought_number": 3,
  "assumptions_challenged": [
    "the regression is cache-miss cost",
    "order_total is the source of truth for the order's value"
  ]
}
```

### 5 — test the fix against the evidence that must also hold

```json
{
  "thought": "Eager-loading the association in the checkout query (one join, no schema change) takes staging from 47 round-trips to 2 and p95 to 210ms on the replayed traffic. The reading also has to explain the other symptom: GET /orders/{id} shows the same 47-query shape and the same p95 step on the same release, and it shares the serializer. It does. The cache removal is a real but separate cost -- p50 moved 95ms -> 130ms, which is the size of that -- and it does not explain the p95.",
  "thought_number": 5,
  "total_thoughts": 6,
  "next_thought_needed": true,
  "stage": "Synthesis",
  "session": "checkout-service",
  "tags": ["orders.checkout", "latency-regression"]
}
```

### 6 — conclude, and hand it to the real gate

```json
{
  "thought": "Cause: an N+1 from the serializer change in 4c1f9a2, not the cache removal. Fix: eager-load the line items on both endpoints; no migration, so it fits before the release train. What this licenses is opening that PR -- nothing more. The verdict belongs to the load test on the replayed traffic and to review; if the load test does not reproduce the 210ms, this chain was wrong a second time.",
  "thought_number": 6,
  "total_thoughts": 6,
  "next_thought_needed": false,
  "stage": "Conclusion",
  "session": "checkout-service",
  "tags": ["orders.checkout", "latency-regression"],
  "assumptions_challenged": ["a story that fits the release diff is a diagnosis"]
}
```

The Conclusion is copied into the PR description and the incident note. The chain itself is not the
deliverable.

---

## Example B — price and volume, explored as branches

ACME's shares rose 18% over Q3 2025 while average daily volume ran at 3x the trailing year. Two
readings fit that signature, and the chain's job is to kill one of them.

### 1–2 — frame, then gather the figures

```json
{
  "thought": "Question: what explains ACME's Q3 2025 move -- +18% price on 3x average daily volume? An answer counts only if every figure in it is traceable to a filing or exchange data, and only if it survives the competing reading rather than merely fitting the one I started with. Out of scope: whether to buy or sell anything.",
  "thought_number": 1,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Problem Definition",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"]
}
```

```json
{
  "thought": "Exchange data: ADV 4.2M shares in Q3 vs 1.4M trailing-year average; the price gain is concentrated in 6 sessions, all within 3 days of the 10-Q. From the Q3 10-Q: unit shipments +9% YoY, ASP +8% YoY, inventory -22% QoQ, and the backlog disclosure in MD&A is +14% QoQ.",
  "thought_number": 2,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Research",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"],
  "axioms_used": ["every figure cites its source document"]
}
```

### 3–4 — one reading, then the admission that two fit

```json
{
  "thought": "First reading: shipments up and inventory down together say the company sold more than it built, and ASP rose at the same time. That is the shape of demand outrunning supply, and the volume spike is the market repricing it after the 10-Q.",
  "thought_number": 3,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"]
}
```

```json
{
  "thought": "But a supply shock produces the same three numbers at ACME: if industry capacity fell, ASP rises, inventory drains, and ACME's own shipments can still print +9% while the industry shrinks. Price+volume alone cannot separate the two, so I am forking rather than continuing: each branch has to name evidence that would only exist under it. Raising the scope to 7 to cover both branches and the thought that closes them.",
  "thought_number": 4,
  "total_thoughts": 7,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"],
  "assumptions_challenged": ["inventory down plus ASP up is by itself evidence of demand"]
}
```

### 5 / 6 — the two branches

```json
{
  "thought": "Branch demand-shift: if end demand rose, industry-wide unit volume should be up for the quarter, ACME's backlog should be up, and ACME's share of industry units should be flat to up. Backlog is +14% QoQ (10-Q MD&A), which is consistent so far.",
  "thought_number": 5,
  "total_thoughts": 7,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"],
  "branch_from_thought": 4,
  "branch_id": "demand-shift"
}
```

```json
{
  "thought": "Branch supply-shock: if capacity fell, industry-wide unit volume should be DOWN for the quarter with ASP up across every vendor, and ACME's share should be roughly flat -- it would be selling scarcity, not winning demand. This branch also predicts competitor inventories draining in the same quarter.",
  "thought_number": 6,
  "total_thoughts": 7,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"],
  "branch_from_thought": 4,
  "branch_id": "supply-shock"
}
```

### 7 — converge on the mainline

A branch is only worth opening if a later mainline thought closes it with evidence.

```json
{
  "thought": "Industry unit shipments for Q3 are +6% (trade association quarterly, table 2), not down, and ACME's unit share rose 1.2pt over the same quarter. That kills branch supply-shock: it predicted an industry contraction that did not happen. demand-shift survives, with the narrower claim the evidence actually supports -- demand up industry-wide, ACME taking share, and the volume spike being repricing concentrated around the 10-Q. Not carried forward: whether any of this is already in the price. This goes to the review and reconciliation step as a reading, not as a recommendation.",
  "thought_number": 7,
  "total_thoughts": 7,
  "next_thought_needed": false,
  "stage": "Conclusion",
  "session": "ACME-2025Q3",
  "tags": ["ACME", "price-volume"],
  "assumptions_challenged": ["the reading I formed first is the one to defend"]
}
```

Note what the chain did *not* do: it did not issue a recommendation. It produced a reading whose
figures someone else can check against the same sources.

---

## Example C — a manuscript's continuity, carried across a session boundary

Chapter 12 of a novel has to land a confrontation. Before writing it, the chain reconstructs what
each character knows by then and which promises to the reader are still unpaid — and the writing
session ends before the chapter does.

### 1 — frame it

```json
{
  "thought": "Before drafting ch12 I need two lists: what each of Maren, Ines and the steward knows by the end of ch11, and which promises made to the reader are still unpaid. An item only counts if it cites the chapter and paragraph where it was established -- what I remember the book saying is not evidence of what the book says.",
  "thought_number": 1,
  "total_thoughts": 4,
  "next_thought_needed": true,
  "stage": "Problem Definition",
  "session": "thornfield-manuscript",
  "tags": ["ch12", "continuity"]
}
```

### 2 — read the manuscript, not the memory of it

```json
{
  "thought": "Established: Maren reads the letter in ch4 p3 but its contents are never shown on the page; she lies to Ines about having read it in ch7 p11; Ines tells the steward she saw Maren at the east door in ch9 p6, which the steward does not act on. Unpaid promise: ch9 p2 tells the reader the locked room will be opened 'before the thaw', and ch12 is the last chapter set in winter.",
  "thought_number": 2,
  "total_thoughts": 4,
  "next_thought_needed": true,
  "stage": "Research",
  "session": "thornfield-manuscript",
  "tags": ["ch12", "continuity"]
}
```

### 3 — a constraint the draft plan did not know about

```json
{
  "thought": "The draft plan has Ines quoting the letter back at Maren, and that is not available: the contents were never on the page (ch4 p3), so quoting them either breaks the reader's access or retroactively rewrites ch4. Raising the scope -- the locked-room promise now has to be placed inside this same chapter, and the order of the two beats is itself a decision rather than a detail.",
  "thought_number": 3,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Analysis",
  "session": "thornfield-manuscript",
  "tags": ["ch12", "continuity"],
  "assumptions_challenged": ["the letter's contents are known to the reader"]
}
```

### 4 — one ordering that satisfies both

```json
{
  "thought": "Ordering that holds: the room is opened first, which gives Ines a fact she can confront Maren with WITHOUT the letter's contents, and Maren's ch7 p11 lie becomes the thing that breaks rather than the letter. That pays the ch9 p2 promise inside the winter chapters and keeps the letter sealed for the ch15 reveal. Checked against the steward: he still has no reason to act, consistent with ch9 p6.",
  "thought_number": 4,
  "total_thoughts": 5,
  "next_thought_needed": true,
  "stage": "Synthesis",
  "session": "thornfield-manuscript",
  "tags": ["ch12", "continuity"]
}
```

### 5 — conclude, and carry the chain across the break

```json
{
  "thought": "Ch12 order: locked room, then confrontation on the lie, letter stays sealed. The session ends here with the chapter undrafted, so I am calling export_session with file_path 'ch12-continuity.json' -- it lands in this session's own exports/ on the server host -- and on resume I import it back into thornfield-manuscript and nothing else, because import replaces a session's history rather than merging into it. What survives this work is the chapter; this chain is the notebook that got me to it.",
  "thought_number": 5,
  "total_thoughts": 5,
  "next_thought_needed": false,
  "stage": "Conclusion",
  "session": "thornfield-manuscript",
  "tags": ["ch12", "continuity"]
}
```
