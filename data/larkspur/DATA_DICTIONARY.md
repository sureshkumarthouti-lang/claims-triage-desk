# Data Dictionary

## incoming_claims/SUB-xxxx/
| File | Description |
|---|---|
| `manifest.json` | submission_id, channel (`email`, `agent_email`, `web_form`), received_at (ISO 8601 with offset), file list |
| `intake_email.txt` | Email channels: From/To/Date/Subject/Attachments headers, then the body |
| `fnol_web_form.pdf`, `web_submission.json` | Web channel: the portal's PDF confirmation and the same fields as JSON |
| `IMG_*.jpg` | Photos with EXIF: DateTimeOriginal, GPS, Make/Model, sometimes UserComment |
| `*Estimate*.pdf`, `*Quote*.pdf`, `*Invoice*.pdf` | Repair estimates/invoices with line items (description, qty, unit, unit price, amount) and notes |
| `*Report*.pdf` | Police crash/theft/burglary reports or fire incident report (two are image-only scans) |
| `MRMC_Statement_*.pdf` | Itemized ER bill (contains health information) |
| `Stolen_Items_List.pdf`, `Contents_Inventory_*.pdf` | Inventories with values and proof notes |
| `Appraisal_*.pdf` | Jewelry appraisals |
| `Receipt_*.jpg`, `payment_confirmation.png` | Photographed receipts / screenshot |

## mock_systems/
| File / table | Key fields |
|---|---|
| `policies.json` (full) / `policies.csv` (flat) / table `policies` | policy_number, line (AUTO/HOME), status (ACTIVE/CANCELLED), named_insureds, phone, email, addresses, term_effective/term_expiration, original_inception, cancellation (effective, reason), coverages, deductibles (home: all_peril, wind_hail), endorsements, scheduled_items, change_history, payment_history, agent |
| table `policy_vehicles` | policy_number, veh_no, year, make, model, vin, plate, garaging_zip |
| table `policy_changes` / `policy_payments` / `scheduled_items` | Coverage changes, payment history, scheduled jewelry |
| `claims_history.csv` / table `claims` | claim_number, policy_number, date_of_loss, reported_date, loss_cause, description, status (OPEN/CLOSED), paid_amount, adjuster, reported_by |
| `claim_photo_index.csv` / table `claim_photos` | claim_number, file_name, sha256, dhash (64-bit difference hash, hex), exif_datetime_original; images in `claim_photos/` |
| `vehicle_values.csv` / table `vehicle_values` | vin, mileage, condition, acv |
| `vendors.csv` / table `vendors` | vendor_id, name, type, drp (network shop), siu_watchlist, watchlist_note, lat/lon |
| `repair_benchmarks.csv` / table `repair_benchmarks` | code, category, item, unit, low, high, midpoint (Central VA 2026) |

## ground_truth/expected_results.json (one object per submission)
| Field | Meaning |
|---|---|
| reporter {name, relationship} | Who submitted (named_insured, agent, family_member) |
| policy_number, line, insured_name | Identified policy |
| date_of_loss, time_of_loss, loss_location | Facts of loss |
| loss_cause | collision, glass, hail, wind, theft, burglary, vandalism, animal_contact, fire, water_sudden, water_gradual, flood |
| asset, loss_summary | What was damaged; one-sentence summary |
| injuries_reported, third_party_involved, police_report_number | Booleans / report or incident number |
| estimate_total | Sum of all estimates/invoices in the package |
| amounts | estimate_total, contents_claimed, medical_billed, vehicle_acv |
| coverage {policy_in_force, coverage_status, applicable_coverages, deductible, cited_sections, notes} | coverage_status: COVERED, PARTIAL, POSSIBLE_EXCLUSION, NOT_IN_FORCE, COVERAGE_NOT_PURCHASED, UNDETERMINED |
| fraud_indicators [{code, severity, evidence}] | Codes from LM-SIU-07 (C1-C4 critical, M1-M8 moderate) |
| duplicate_of | Existing claim number, if a duplicate |
| missing_fields | Required elements still unknown (PENDING_INFO cases) |
| route, route_rule, route_reason | FAST_TRACK / STANDARD / SPECIALIST / SIU / PENDING_INFO and the LM-CHG-2026 rule (R1-R6) |
| prompt_injection_detected, injection_locations | Whether the package contains manipulation attempts and where |
| pii_detected | Sensitive data types present that must be masked |

## evals/
| File | Use |
|---|---|
| `claim_intake_cases.jsonl` | One case per submission with expected fields and a scoring plan (exact, numeric, set-F1, LLM-judge) |
| `rag_golden_qa.jsonl` | 30 questions with expected answers and source sections, for RAG metrics |
| `guardrail_injection_cases.jsonl` | 16 texts (12 attacks, 4 benign controls) with expected behavior |
| `pii_masking_cases.jsonl` | 14 input/expected-output pairs for the masking guardrail |
