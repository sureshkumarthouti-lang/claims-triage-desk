# Larkspur Mutual - Claims Intake & Triage Capstone Dataset

A complete, **synthetic** dataset for building and evaluating an AI claims intake agent for a fictional insurer, **Larkspur Mutual Insurance Company**. Everything here - the company, people, policies, shops, police agencies, phone numbers (555-01xx) and email domains (example.com/.net/.org) - is made up. SSNs, bank numbers and license numbers are deliberately invalid.

## The business problem (one paragraph)
Larkspur receives new auto and home claims by email, web form and agent submission. Staff read every email and attachment, retype the details, check the policy, look for fraud and decide who handles the claim. Your agent does that first pass: it reads the claim package, extracts a structured claim record, checks the policy and coverage wording, screens for fraud indicators, and routes the claim to **FAST_TRACK, STANDARD, SPECIALIST, SIU or PENDING_INFO** - while a human adjuster still makes every coverage, denial and payment decision.

## What's inside
| Folder | What it is | Course concept it feeds |
|---|---|---|
| `knowledge_base/policy_forms/` | Personal Auto Policy (LM-PA-01) and Homeowners Policy (LM-HO-03), PDF + Markdown | **RAG** - chunk and embed into **Chroma** |
| `knowledge_base/guidelines/` | Claims Intake & Routing Guidelines (LM-CHG-2026) and SIU Fraud Indicators Guide (LM-SIU-07) | **RAG** + **system prompt** rules |
| `knowledge_base/declarations/` | 24 policy Declarations pages (PDF) | RAG or document lookup |
| `mock_systems/` | Policy system, claims history, vehicle values, vendors, repair benchmarks, prior-claim photo hashes - as JSON/CSV **and** one SQLite DB (`larkspur_mock.db`) | **MCP tool servers** / **tool calling** |
| `incoming_claims/SUB-1001 ... SUB-1022/` | 22 claim packages: intake email or web form, photos (JPEG with EXIF), estimates, police/fire reports, medical bill, receipts, inventories, appraisals | Agent **inputs** - multimodal extraction, **structured outputs** |
| `schemas/claim_intake_result.schema.json` | JSON Schema for the agent's output | **Structured outputs** (Pydantic) |
| `ground_truth/` | Answer key for all 22 submissions + scenario matrix | **DeepEval** regression tests |
| `evals/` | Ready-to-use eval sets (intake cases, RAG Q&A, prompt-injection cases, PII masking cases) | **DeepEval / LLM-as-judge**, **guardrails** |
| `tools/generator/` | Python source that generated everything (edit and re-run to add claims) | - |

Mix of submissions: 22 total (14 auto, 8 home) - 4 fast-track, 12 standard, 3 specialist, 2 SIU, 1 pending-info. Several contain deliberate traps (coverage exclusions, a duplicate, prompt injections, PII, fraud signals hidden in photo metadata and receipts).

> **Keep `ground_truth/` and `evals/` out of the agent's context.** They are the answer key. Point the agent only at `knowledge_base/`, `mock_systems/` (through tools) and one `incoming_claims/SUB-xxxx/` folder at a time.

## Suggested architecture (maps to every course concept)
1. **Router (routing pattern)** - read `manifest.json`; classify channel and line of business (auto/home).
2. **Extractor (Claude + structured outputs)** - read the email/web form, PDFs and photos (Claude vision); produce the fields in `schemas/claim_intake_result.schema.json`.
3. **Policy & systems tools (MCP + tool calling, ReAct loop)** - look up the policy, claim history, vehicle value, vendor watch list, benchmarks and photo hashes.
4. **Coverage analyst (RAG over Chroma)** - retrieve the policy wording and guidelines; cite sections like `LM-PA-01 §D.2`.
5. **Fraud screener (orchestrator-worker)** - parallel workers check photo EXIF, estimate vs benchmark, claim frequency, vendor watch list, receipts; apply LM-SIU-07 §3.
6. **Router decision + reflection** - apply LM-CHG-2026 §5 rules R1-R6; a reviewer agent checks the decision against the rules before finalizing.
7. **Human-in-the-loop (LangGraph interrupt)** - an adjuster approves the route for anything not FAST_TRACK.
8. **Guardrails** - mask PII in notes (LM-CHG-2026 §10); detect and ignore embedded instructions (§11).
9. **Observability (Langfuse)** - trace every step, tool call, token cost and latency per submission.
10. **Evals (DeepEval)** - run all 22 submissions against `ground_truth/expected_results.json` on every change.

You can build the backbone in **LangGraph** and implement one worker (for example, the fraud screener) with the **OpenAI Agents SDK** if your course expects both.

## Suggested MCP tools
| Tool | Backed by | Returns |
|---|---|---|
| `lookup_policy(policy_number)` | `policies` table / `policies.json` | Full policy incl. status, cancellation, vehicles, coverages, endorsements, change and payment history |
| `search_policies(name, phone, email, address)` | `policies` | Candidate policies (match on 2+ identifiers) |
| `get_claim_history(policy_number)` | `claims` / `claims_history.csv` | Prior and open claims |
| `find_possible_duplicates(policy_number, date_of_loss, loss_cause)` | `claims` | Open claims within +/-2 days |
| `get_vehicle_value(vin)` | `vehicle_values` | Actual cash value (ACV) |
| `lookup_vendor(name)` | `vendors` | DRP status, SIU watch-list flag, location |
| `get_benchmarks(category)` / `check_estimate(lines)` | `repair_benchmarks` | Low/high/midpoint per item; benchmark total |
| `read_photo_metadata(path)` | the JPEG files | EXIF capture time, GPS, camera, user comment |
| `check_photo_reuse(sha256, dhash)` | `claim_photos` / `claim_photo_index.csv` | Matching prior-claim photos |
| `register_claim(record)` / `route_claim(id, route)` | your own table | Writes the intake result (mock) |

## Evaluation ideas
- **Routing accuracy** - exact match on `route` (the headline metric).
- **Extraction** - exact match on policy number, date of loss, loss cause, police report number; numeric match on estimate total and deductible.
- **Coverage reasoning** - exact match on `coverage_status`; LLM-as-judge (GEval) on coverage notes and cited sections.
- **Fraud screening** - precision/recall on indicator codes (`fraud_indicator_codes`).
- **Guardrails** - injection detected on SUB-1012 and SUB-1016 without the route changing; zero unmasked SSN/bank/DOB/health data in `adjuster_notes` (`evals/pii_masking_cases.jsonl`, `evals/guardrail_injection_cases.jsonl`).
- **RAG** - faithfulness, answer relevancy and contextual recall on `evals/rag_golden_qa.jsonl`.

## Notes
- **Photos** are stylized illustrations drawn in code (no real photos of real damage). They are clear enough for vision models to describe the damage, and their EXIF metadata (capture time, GPS, camera, user comments) is realistic and part of the test. If you want photorealistic images for a demo, you can swap in images from a public car-damage dataset - keep the file names and re-apply the EXIF.
- **Two police reports are scanned images** (SUB-1005, SUB-1019): there is no text layer, so your pipeline needs OCR or vision.
- **Dates**: the dataset is set in Sept-Nov 2026. "Today" for intake purposes is the `received_at` time in each `manifest.json`.
- **Section citations** use the numbering printed in the documents, e.g. `LM-PA-01 §D.4(1)`, `LM-HO-03 §I.7(3)(a)`, `LM-CHG-2026 §5`.
